# GitOps Demo: Kubernetes + Argo CD

A small Python web application showing its message, version, and pod name. No Python packages or database are required. This is a learning starter, with two replicas, resource limits, health probes, and an unprivileged container.

## Requirements

- Kubernetes cluster and kubectl configured for it.
- Argo CD already installed in namespace `argocd`, with permission to deploy through its `default` project.
- Docker, a Git repository with branch `main`, and a container registry reachable from the cluster.
- For the simplest setup, use a public Git repository and public image. For private Git, configure repository credentials in Argo CD; for private images, create a registry pull secret in `gitops-demo` and add `imagePullSecrets` to the pod spec. Do not commit credentials to Git.

## 1. Publish the container

Run from this project's root. Replace `YOUR_REGISTRY` with your registry/account, such as `docker.io/yourname`.

```bash
docker login
docker build -t YOUR_REGISTRY/gitops-demo:1.0.0 .
docker push YOUR_REGISTRY/gitops-demo:1.0.0
```

Build an image matching the cluster's CPU architecture. For mixed clusters, use Docker Buildx to publish a multi-platform image.

## 2. Configure and push Git

Edit `k8s/deployment.yaml`: replace `YOUR_REGISTRY/gitops-demo:1.0.0` with the image you pushed.

Edit `argocd/application.yaml`: replace `repoURL` with your actual Git repository URL. Keep `path: k8s` if you upload this project's contents at the repository root. If nested, change `path` to the corresponding folder, such as `gitops-demo/k8s`.

For a new, empty remote repository:

```bash
git init -b main
git add .
git commit -m "Add GitOps demo application"
git remote add origin https://github.com/YOUR_USER/gitops-demo.git
git push -u origin main
```

## 3. Register the application once

```bash
kubectl apply -f argocd/application.yaml
kubectl get application gitops-demo -n argocd -w
```

Argo CD reads `k8s/` from Git, creates the destination namespace, and reconciles the Deployment, Service, and ConfigMap. Wait for `Synced` and `Healthy`. The Application manifest is a one-time bootstrap; its own later changes require reapplying it unless you manage it through a parent Argo CD application.

## 4. Open the app

Once Argo CD has synced:

```bash
kubectl rollout status deployment/gitops-demo -n gitops-demo --timeout=180s
kubectl port-forward -n gitops-demo svc/gitops-demo 8080:80
```

Open http://localhost:8080. This starter uses local port forwarding. Add an Ingress or LoadBalancer separately for external access.

## 5. Demonstrate GitOps

Change the message in `k8s/configmap.yaml`, then:

```bash
git add k8s/configmap.yaml
git commit -m "Update welcome message"
git push
```

Argo CD detects the commit during polling, or you can click Refresh in its UI. After synchronization, Kubernetes eventually refreshes the mounted ConfigMap; refresh the browser to see the message. The app reads the file per request, so no pod restart is needed. Allow a few minutes for polling and volume propagation.

For a code release, build and push a new image tag (for example `1.0.1`), update the Deployment's `image` and `APP_VERSION`, then commit and push. Argo CD deploys the published image; it does not build images. Avoid reusing tags; immutable digests are preferable for production. Roll back by reverting the release commit and pushing it.

`prune: true` removes resources deleted from Git. `selfHeal: true` corrects manual drift. `allowEmpty: false` protects against an empty desired resource set. Keep intended changes in Git.

## Local run and troubleshooting

```bash
python3 app/server.py
# Open http://localhost:8080
```

If a deployment is stuck, inspect:

```bash
kubectl get pods -n gitops-demo
kubectl describe pods -n gitops-demo
kubectl logs -n gitops-demo deployment/gitops-demo
kubectl get application gitops-demo -n argocd -o yaml
```

`ImagePullBackOff` usually requires correcting the image path, publishing the image, or configuring registry access. Repository errors require checking the Git URL, branch, directory, or Argo CD repository credentials.

Official references:
- https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/
- https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-probes/

Validation of this package covered local HTTP behavior and manifest structure. Container build and live Kubernetes deployment require your own registry and cluster.
# gitops
