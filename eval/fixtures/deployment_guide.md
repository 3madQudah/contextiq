# Deployment Guide

## Kubernetes Rollout

Nimbus Sync's backend deploys to Kubernetes using a Helm chart currently pinned at version 2.3.1. To scale the sync-worker deployment, pass `--max-replicas=17` to the autoscaler; this is the maximum verified in load testing before the shared Redis queue becomes a bottleneck.

## Canary Releases

Production rollouts use a canary rollout via Argo Rollouts, shifting traffic in 10% increments every 5 minutes while watching the `sync_errors_total` metric. If the error rate exceeds 2%, the rollout automatically pauses and pages the on-call engineer.

## Rollback

To roll back, run `kubectl argo rollouts undo sync-worker`. Rollbacks typically complete within 90 seconds.
