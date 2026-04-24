#!/bin/bash
# wlan0クライアントから port 5400 (media-kanri) を許可
sudo iptables -A INPUT -i wlan0 -p tcp --dport 5400 -j ACCEPT
sudo iptables -A INPUT -i wlan0 -p tcp --dport 80 -j ACCEPT
# 永続化
sudo netfilter-persistent save
