#!/bin/bash

# 清理pod
kubectl delete pod busybox1 --force
kubectl delete pod busybox2 --force
kubectl delete pod busybox3 --force
