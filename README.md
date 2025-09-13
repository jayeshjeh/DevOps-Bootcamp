# README.md

## 1. Prerequisites

To get started, install the following on your host machine:

* **Vagrant**: [Download & Install](https://developer.hashicorp.com/vagrant/downloads)
* **VirtualBox**: [Download & Install](https://www.virtualbox.org/wiki/Downloads)

Ensure both are installed and available in your system PATH.

---

## 2. Starting the Vagrant VM

### Boot the VM

```bash
vagrant up --provider=virtualbox
```

This will:

* Create the VM from the `Vagrantfile`
* Install dependencies via the `install.sh` provisioning script
* Spin up Docker and run your services using `docker-compose`

### Re-provision after changes to shell script

If you update the provisioning script (e.g., `install.sh`):

```bash
vagrant reload --provision-with shell
```

This reloads the VM and re-runs the shell provisioner.

### SSH into the VM

To log into the guest VM:

```bash
vagrant ssh
```

Inside, you can:

```bash
cd /vagrant   
```

Run docker commands, for example:

```bash
docker ps -a
```

---

## 3. Running and Scaling the API

Your **Makefile** includes:

```make
make start-api
```

This command:

* Starts Postgres
* Applies migrations
* Runs the API service with **2 replicas** (`api=2`)
* Starts Nginx as a load balancer

So you have 2 API containers running behind Nginx.

---

## 4. Accessing Endpoints

Once VM is up:

* Health check endpoint:

  ```
  http://localhost:8080/api/v2/health
  ```
* Student endpoints (CRUD):

  * `GET /api/v2/students`


To check if all containers are running:

```bash
docker ps
```

You should see: `postgres_db`, `nginx`, and two replicas of `flask_api`.

---

## 5. Running the Postman Collection

1. Open **Postman**.
2. Import the provided JSON file

   * In Postman → File → Import → Choose JSON file.

4. Run the collection to test all endpoints.

---

## 6. Useful Vagrant Commands

* Suspend the VM:

  ```bash
  vagrant suspend
  ```
* Halt (shutdown) the VM:

  ```bash
  vagrant halt
  ```
* Destroy the VM:

  ```bash
  vagrant destroy -f
  ```
* Check status:

  ```bash
  vagrant status
  ```

---

## 7. Troubleshooting

* If endpoints don’t respond, check Nginx logs:

  ```bash
  docker logs nginx
  ```
* If DB is unhealthy, check Postgres logs:

  ```bash
  docker logs postgres_db
  ```

