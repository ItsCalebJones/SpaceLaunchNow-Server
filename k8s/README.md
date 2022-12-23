# SLN k8s Deployment

### 1) Setup secrets 
Add secret for Cloudflare API Token 
```
kubectl create secret generic cloudflare-api-token-secret --from-literal=api-token=
```

### 2) Get repositories for helm packages installed
```
helm repo add jetstack https://charts.jetstack.io
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
```

### 3) Install cert-manager and nginx-ingress
(this will add DO load balancer)
```
helm install cert-manager jetstack/cert-manager --version v1.5.5 --set installCRDs=true
helm install nginx-ingress ingress-nginx \
--repo https://kubernetes.github.io/ingress-nginx \
--namespace ingress-nginx \
--set controller.metrics.enabled=true \
--set controller.publishService.enabled=true \
--set-string controller.podAnnotations."prometheus\.io/scrape"="true" \
--set-string controller.podAnnotations."prometheus\.io/port"="10254" \
--set-string controller.config.use-forwarded-headers=true,controller.config.log-format-upstream='$http_x_forwarded_for $remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" $request_length $request_time [$proxy_upstream_name] [$proxy_alternative_upstream_name] $upstream_addr $upstream_response_length $upstream_response_time $upstream_status $req_id'
```

### 4) Add Name to Loadbalancer
Edit the LoadBalancer resource and add the following in the annotations:
`service.beta.kubernetes.io/do-loadbalancer-name: sln-prod-k8s-lb`

```
kubectl edit service/nginx-ingress-ingress-nginx-controller -n ingress-nginx
```

### 5) Install memcached for SLN
```
helm install sln-prod bitnami/memcached
```

### 6) Setup SLN
Note: There are two values files. The `values.yaml` file is the standard deployment which will be used by the prod db. The `values-dev.yaml` file contains the dev overrides. 
```
helm install $RELEASE_NAME k8s/helm/ --namespace=$STAGING_NAMESPACE --values k8s/helm/values.yaml
```


### 7) Setup ingress & certs
The domains are defined here and therefore may need to be changed
```
cd ../ingress/issuer
kubectl apply -f issuer.yaml
kubectl apply -f certificate.yaml
```

```
cd ..
kubectl apply -f ingress.yaml
```

Monitor cert issuer
```
kubectl describe certificate spacelaunchnowme-tls
```
