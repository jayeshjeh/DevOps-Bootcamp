# Vault + External Secrets Operator (ESO) + Postgres (Dev) + App via Helm + ArgoCD via Helm

A minimal, **sequence-first** guide to get Vault (dev) working with ESO, sync credentials for Postgres, deploy your **Flask API via Helm**, and install **ArgoCD via Helm**. Kept to only what’s required.

---

## 0) Prereqs

* `kubectl` and `helm` configured
* Namespaces: `vault`, `external-secrets`, `student-api`, `argocd`

```bash
kubectl create ns vault --dry-run=client -o yaml | kubectl apply -f -
kubectl create ns external-secrets --dry-run=client -o yaml | kubectl apply -f -
kubectl create ns student-api --dry-run=client -o yaml | kubectl apply -f -
kubectl create ns argocd --dry-run=client -o yaml | kubectl apply -f -
```

---

## 1) Install Vault (DEV MODE) — **one command**

> Dev mode is in-memory (no PVCs), HTTP on 8200, fixed root token, injector disabled.

```bash
helm upgrade --install vault hashicorp/vault \
  -n vault --create-namespace \
  --set "global.enabled=true" \
  --set "global.tlsDisable=true" \
  --set "server.dev.enabled=true" \
  --set "server.dev.devRootToken=dev-only-token" \
  --set "injector.enabled=false"
```

**Verify**

```bash
kubectl -n vault get pods,svc | grep vault
kubectl -n vault logs deploy/vault | tail -n 40
```

---

## 2) Seed secrets in Vault (KV v2 at `secret/`)

```bash
kubectl -n vault exec -ti deploy/vault -- sh -lc '
export VAULT_ADDR=http://127.0.0.1:8200
export VAULT_TOKEN=dev-only-token
vault kv put secret/app-secrets \
  POSTGRES_USER=User1 \
  POSTGRES_PASSWORD=User1password \
  DATABASE_URL="postgresql+psycopg://User1:User1password@postgres.student-api.svc.cluster.local:5432/postgres_db"'
```

---

## 3) Install External Secrets Operator (with CRDs)

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
helm upgrade --install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace \
  --set installCRDs=true
kubectl -n external-secrets get pods
```

---

## 4) Create Vault token Secret for ESO (dev token)

> Keep tokens out of YAML; store them in a Secret and reference it.

```bash
kubectl -n external-secrets create secret generic vault-token \
  --from-literal=token=dev-only-token
```

---

## 5) Create `ClusterSecretStore` (ESO → Vault)

Use **apiVersion `external-secrets.io/v1`**.

```yaml
# clustersecretstore.yaml
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: vault-cluster
spec:
  provider:
    vault:
      server: "http://vault.vault.svc:8200"
      path: "secret"
      version: "v2"
      auth:
        tokenSecretRef:
          name: vault-token
          key: token
          namespace: external-secrets
```

```bash
kubectl apply -f clustersecretstore.yaml
kubectl get clustersecretstore vault-cluster -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}{"\n"}{.status.conditions[?(@.type=="Ready")].message}{"\n"}'
```

---

## 6) ExternalSecret → create app Secret in `student-api`

```yaml
# externalsecret-db.yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: db-secrets
  namespace: student-api
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-cluster
  target:
    name: db-secrets
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef: { key: app-secrets, property: POSTGRES_USER }
    - secretKey: password
      remoteRef: { key: app-secrets, property: POSTGRES_PASSWORD }
    - secretKey: postgres-password
      remoteRef: { key: app-secrets, property: POSTGRES_PASSWORD }
    - secretKey: DATABASE_URL
      remoteRef: { key: app-secrets, property: DATABASE_URL }
```

```bash
kubectl apply -f externalsecret-db.yaml
kubectl -n student-api get externalsecret db-secrets -o wide
kubectl -n student-api get secret db-secrets -o yaml
```

---

## 7) Postgres (Bitnami) — consume the synced Secret

Values (`values-postgres.yaml`):

```yaml
fullnameOverride: postgres
architecture: standalone

primary:
  nodeSelector:
    node-type: database
  persistence:
    enabled: true
    size: 1Gi
    storageClass: "csi-hostpath-sc"

auth:
  existingSecret: db-secrets
  username: "User1"
  database: "postgres_db"

service:
  ports:
    postgresql: 5432
```

Install:

```bash
helm upgrade --install postgres oci://registry-1.docker.io/bitnamicharts/postgresql \
  -n student-api --create-namespace -f values-postgres.yaml
kubectl -n student-api get pods,svc,pvc
```

---

## 8) Deploy your **Flask API via Helm** (uses `db-secrets`)

Assuming your chart lives at `helm/student-api` and reads env from the Secret:

**Example minimal values (`helm/student-api/values.yaml`):**

```yaml
image:
  repository: jayesh898/flask-api
  tag: v1.0.1
  pullPolicy: IfNotPresent

replicaCount: 2

service:
  type: ClusterIP
  port: 5000

envFromSecrets:
  - name: db-secrets  # your template should map this to envFrom.secretRef

nodeSelector:
  node-type: application
```

**Install/upgrade app:**

```bash
helm upgrade --install student-api ./helm/student-api \
  -n student-api \
  --set image.repository=jayesh898/flask-api \
  --set image.tag=v1.0.1

kubectl -n student-api get deploy,svc,pod
```

> If your chart doesn’t yet support `envFromSecrets`, update the Deployment template to include:
>
> ```yaml
> envFrom:
>   - secretRef:
>       name: db-secrets
> ```

---

## 9) **ArgoCD via Helm** (optional, for GitOps)

Install ArgoCD using the official Argo Helm repo:

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

helm upgrade --install argocd argo/argo-cd \
  -n argocd --create-namespace \
  --set controller.nodeSelector.node-type=dependent_services \
  --set server.nodeSelector.node-type=dependent_services \
  --set repoServer.nodeSelector.node-type=dependent_services \
  --set redis.nodeSelector.node-type=dependent_services
```

# Argo CD & Flask API Deployment (via Helm)

This guide walks through a complete setup of **Argo CD** using Helm, followed by deploying your **Flask API Helm chart** automatically using an Argo CD `Application` manifest.

---

## 1. Prerequisites

Ensure you have:

* A running Kubernetes cluster (e.g., multi-node Minikube)
* `kubectl` and `helm` installed
* Internet access for pulling charts and images

---

## 2. Install Argo CD using Helm

### Step 1: Add the Argo Helm repository

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
```

### Step 2: (Optional) Create custom values file

Create a file `values-argocd.yaml` to pin ArgoCD components to your `dependent_services` node:

```yaml
global:
  nodeSelector:
    node-type: dependent_services

controller:
  nodeSelector:
    node-type: dependent_services

repoServer:
  nodeSelector:
    node-type: dependent_services

server:
  nodeSelector:
    node-type: dependent_services
  service:
    type: ClusterIP

applicationSet:
  nodeSelector:
    node-type: dependent_services
```

### Step 3: Install Argo CD

```bash
helm upgrade --install argocd argo/argo-cd \
  -n argocd --create-namespace \
  --set crds.install=true \
  -f values-argocd.yaml
```

### Step 4: Verify installation

```bash
kubectl -n argocd get pods
kubectl -n argocd get svc argocd-server
```

### Step 5: Access the Argo CD UI

```bash
kubectl -n argocd port-forward svc/argocd-server 8080:80
```

Visit **[http://localhost:8080](http://localhost:8080)**

Retrieve the admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
```

Use **username:** `admin` and the password above to log in.

---

## 3. Create the Argo CD Application for Flask API

Once Argo CD is running, register your Flask API Helm chart using this manifest.

Save as **`flask-api-app.yaml`**:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: flask-api
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/jayeshjeh/DevOps-Bootcamp.git
    targetRevision: milestone_9
    path: helm/application
    helm:
      releaseName: flask-api
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: student-api
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
```

Apply it:

```bash
kubectl apply -f flask-api-app.yaml
```

Check:

```bash
kubectl -n argocd get applications.argoproj.io
```

You should now see **flask-api** listed in the Argo CD UI.

---

## 4. How Auto-Deployment Works

Once the `Application` is created:

* Argo CD continuously watches the repo path `helm/application` on the branch `milestone_9`.
* Every new commit to that branch triggers Argo CD to detect drift.
* Because of this config:

  ```yaml
  automated:
    prune: true
    selfHeal: true
  ```

  Argo CD automatically deploys the latest chart version, prunes old resources, and heals any drift.

You do **not** need to manually run `helm install` again.

---

## 5. Optional: Remove Old Manual Helm Releases

If you manually installed your app earlier with Helm:

```bash
helm -n student-api ls
helm -n student-api uninstall <old-release-name>
```

Then allow Argo CD to manage the deployment instead.

---

## 6. Verify Deployment

Check all resources in `student-api` namespace:

```bash
kubectl -n student-api get all
```

If everything is healthy, Argo CD UI will show the **Application** as **Synced** and **Healthy**.

---

## ✅ Summary of Commands

```bash
# Install Argo CD
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
helm upgrade --install argocd argo/argo-cd -n argocd --create-namespace -f values-argocd.yaml

# Access Argo CD UI
kubectl -n argocd port-forward svc/argocd-server 8080:80
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo

# Create Flask API application
kubectl apply -f flask-api-app.yaml

# Check status
kubectl -n argocd get applications.argoproj.io
kubectl -n student-api get pods
```

---

**After setup:**

* Any new push to `milestone_9` branch → Argo CD detects and redeploys automatically.
* You can view logs, sync history, and health in the Argo CD UI
