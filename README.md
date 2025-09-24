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


