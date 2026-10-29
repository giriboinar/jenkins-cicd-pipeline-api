# Jenkins setup (local, 10 minutes)

1. Start Jenkins: `docker compose -f jenkins/docker-compose.yml up -d`
2. Open http://localhost:8080 and unlock it with the initial admin password:
   `docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword`
3. Install suggested plugins, then add the ones in `plugins.txt`:
   `docker exec jenkins jenkins-plugin-cli --plugin-file /var/jenkins_home/plugins.txt`
   (copy plugins.txt into the container first, or mount it as a volume).
4. Install Docker CLI and kubectl inside the Jenkins container if the
   Docker Build / Deploy stages need them, or use agents that already
   have them. Trivy must be installed wherever the Security Scan stage runs.
5. Create a Multibranch or Pipeline job pointing at this repo, with the
   Jenkinsfile at the repo root. No credentials are needed for a
   test-through-build run: DOCKER_PUSH and DEPLOY_TO_K8S default to 'false'.
6. To enable push: add a Username/Password credential with ID `docker-hub`
   and set the job parameter DOCKER_PUSH to 'true'. To enable deploy:
   point kubectl at a cluster with a `deployments` namespace and set
   DEPLOY_TO_K8S to 'true'. Never commit credentials — they live only
   in Jenkins credentials, never in git.
