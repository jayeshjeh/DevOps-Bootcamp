# README.md

## Minikube 3-Node Cluster Setup with Labels
---

### 1. Prerequisites

* Linux with Docker installed (or VirtualBox/KVM2 as driver)
* Minikube installed
* kubectl installed 


---

### 2. Start Minikube with 3 nodes

```bash
minikube start -p prod --driver=docker --nodes=4
```

This creates:

* `prod` (control-plane)
* `prod-m02` (worker)
* `prod-m03` (worker)
* `prod-m04` (worker)

Check nodes:

```bash
kubectl get nodes -o wide
```

---

### 3. Add labels to nodes

Attach role-based labels:

```bash
kubectl label node prod-m02 type=application
kubectl label node prod-m03 type=database
kubectl label node prod-m04 type=dependent_services
```

Verify:

```bash
kubectl get nodes --show-labels
```

---

### 4. Use labels in workloads

Example Deployment pinned to `type=application` node:

```yaml
spec:
  template:
    spec:
      nodeSelector:
        type: application
```

---

### 5. Confirm placement

Check where pods are scheduled:

```bash
kubectl get pods -o wide
```

Check node labels:

```bash
kubectl describe node prod-m02 | grep -i labels -A5
```




#  Kubernetes 

---

## 1) External Secrets Operator (ESO)

Install ESO (once):

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update
helm upgrade --install external-secrets external-secrets/external-secrets \
  --namespace external-secrets --create-namespace \
  --set installCRDs=true
```

---

## 2) Vault (dev) and ClusterSecretStore

Apply your manifests:

```bash
kubectl apply -f k8s/vault.yml              
kubectl apply -f k8s/external-secrets.yml  
kubectl -n vault rollout status deploy/vault
```

**Seed secrets into Vault (dev mode) — step by step:**

1. **Open a shell in the Vault pod**

   ```bash
   kubectl -n vault exec -it deploy/vault -- sh
   ```

2. **Inside the pod, set env and enable KV v2**

   ```sh
   export VAULT_ADDR=http://127.0.0.1:8200
   export VAULT_TOKEN=dev-only-token
   vault secrets enable -path=secret kv-v2 || true
   ```

3. **Write your application secrets at `secret/app-secrets`**

   ```sh
   vault kv put secret/app-secrets \
     POSTGRES_USER=User1 \
     POSTGRES_PASSWORD=User1password \
     DATABASE_URL="postgresql+psycopg://User1:User1password@postgres.student-api.svc.cluster.local:5432/postgres_db"
   vault kv get secret/app-secrets
   ```

4. **Exit the pod shell**

   ```sh
   exit
   ```

> Note: Vault **dev** stores data in memory. If the Vault pod restarts, repeat steps 1–3 to re-seed secrets.

---

## 3) Database

Apply DB stack first:

```bash
kubectl apply -f k8s/database.yml
kubectl -n student-api get externalsecret,secret,pvc,pods,svc
```

You should see `db-secrets` created by ESO and the `postgres` pod Running on the database node.

---

## 4) Application

Apply the app (image tag should include your committed migrations):

```bash
kubectl apply -f k8s/application.yml
kubectl -n student-api logs deploy/flask-api -c migrate-container --tail=200
```

---

## 5) Access & test

**Option A — NodePort (as in your Service):**

```bash
MINI_IP=$(minikube ip)
curl -i http://$MINI_IP:30001/api/v2/health
```

**Option B — Port-forward the Service (no NodePort needed):**

```bash
kubectl -n student-api port-forward svc/flask-service 8080:80
# new shell:
curl -i http://127.0.0.1:8080/api/v2/health
```

---

## 6) Migrations (local workflow)

When you change `models.py`:

1. **Have a Postgres running locally** (any Postgres is fine for autogenerate).
2. Set env and run the standard Alembic/Flask-Migrate commands locally:

   ```bash
   export FLASK_APP=wsgi.py
   export DATABASE_URL='postgresql+psycopg://User1:User1password@localhost:5432/postgres_db'
   flask db upgrade              # bring local DB to current head
   flask db migrate -m "<your change>"
   flask db upgrade              # optional local apply to test
   ```
3. **Commit** the new `migrations/` files.
4. **Build & push** a new app image that includes those files.
5. **Update image tag** in `k8s/application.yml` then:

   ```bash
   kubectl apply -f k8s/application.yml
   # or
   kubectl -n student-api set image deploy/flask-api \
     flask-api=jayesh898/flask-api:<NEW_TAG>
   # or 
   Delete yml and reapply.
   ```

The init container will run `flask db upgrade` in the cluster.

---

## 7) Useful commands

**Secrets / ESO status**

```bash
kubectl -n student-api get externalsecret
kubectl -n student-api describe externalsecret app-secrets db-secrets
kubectl -n student-api get secret app-secrets db-secrets
```

**Database (psql)**

```bash
kubectl -n student-api exec -it sts/postgres -c postgres -- \
  bash -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
# inside psql:
# \dt
# select * from alembic_version;
# \d+ <table>
```

**Check migration init container logs**

```bash
kubectl -n student-api logs deploy/flask-api -c migrate-container --tail=200
```

**Check Service / URL**

```bash
kubectl -n student-api get svc flask-service
minikube ip
curl -i http://$(minikube ip):30001/api/v2/health
```


