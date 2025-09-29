# KWS-302WF Aircon Monitor

![Image of the Grafana dashboard](https://i.imgur.com/AqQee6w.jpeg)

One roommate hogging your AC bill? Want cool graphs about your aircons electricity to stare at? Worry no more. 

## Discord
Using Discord, your roommates can turn the AC on and off, and Prometheus will track how much each user used the AC in each billing month. One can calculate how much they will pay by comparing their `avg_over_time()` in promql.

| AC Monitoring | AC Control |
| - | - |
| ![](https://i.imgur.com/W1FbqkI.jpeg) | ![](https://i.imgur.com/wJu7aoQ.jpeg) |

## Grafana
Using the Grafana Prometheus plugin, one can add the `prometheus-scraper`'s port (by default 6060) to Prometheus' scrape list and make cool graphs out of it.
