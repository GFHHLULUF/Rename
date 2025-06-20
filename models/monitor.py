from prometheus_api_client import PrometheusConnect

class PrometheusMonitor:
    def __init__(self, PROMETHEUS_URL):
        self.prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)
        self.timeout = 3

    def change_url(self, new_url):
        self.prom = PrometheusConnect(url=new_url, disable_ssl=True)

    def get_cpu_info(self):
        proc = 0
        info = {}
        query = 'rate(windows_cpu_processor_utility_total{instance="windows-server"}[5s]) / rate(windows_cpu_processor_rtc_total{instance="windows-server"}[5s])'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            for i in range(len(data)):
                proc += float(data[i]['value'][1])
            info['usage_precent'] = proc/ len(data)

        query = 'windows_thermalzone_temperature_celsius'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['temperatur'] = data[0]['value'][1]

        query = 'windows_cpu_info'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['name'] = data[0]['metric']['name']
            info['description'] = data[0]['metric']['description']
        
        query = 'windows_cpu_core_frequency_mhz{core="0,0"}'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['frequency_mhz'] = data[0]['value'][1]

        query = 'windows_cpu_info_core'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['core'] = data[0]['value'][1]

        query = 'windows_cpu_info_thread'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['thread'] = data[0]['value'][1]

        query = 'windows_cpu_info_l2_cache_size'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['L2'] = data[0]['value'][1]

        query = 'windows_cpu_info_l3_cache_size'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['L3'] = data[0]['value'][1]
        
        return info

    def get_RAM_info(self):
        info = {}
        query = '(windows_memory_physical_total_bytes - windows_memory_available_bytes) / windows_memory_physical_total_bytes * 100'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['usage_precent'] = data[0]['value'][1]

        query = 'windows_memory_available_bytes / 1073741824'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['available'] = data[0]['value'][1]

        query = '(windows_memory_physical_total_bytes - windows_memory_available_bytes) / 1073741824'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['use'] = data[0]['value'][1]

        query = 'windows_memory_physical_total_bytes / 1073741824'
        data = self.prom.custom_query(query, timeout=self.timeout)
        if len(data) != 0:
            info['all'] = data[0]['value'][1]
        
        return info

    def get_ROM_info(self):
        disks = {}
        query = '(windows_logical_disk_size_bytes - windows_logical_disk_free_bytes) / windows_logical_disk_size_bytes * 100'
        data = self.prom.custom_query(query, timeout=self.timeout)
        for i in range(len(data)):
            disks[data[i]['metric']['volume']] = {'usage_precent': data[i]['value'][1]}

        query = 'windows_logical_disk_free_bytes / 1073741824'
        data = self.prom.custom_query(query, timeout=self.timeout)
        for i in range(len(data)):
            disks[data[i]['metric']['volume']]['available'] = data[i]['value'][1]

        query = '(windows_logical_disk_size_bytes - windows_logical_disk_free_bytes) / 1073741824'
        data = self.prom.custom_query(query, timeout=self.timeout)
        for i in range(len(data)):
            disks[data[i]['metric']['volume']]['use'] = data[i]['value'][1]

        query = 'windows_logical_disk_size_bytes / 1073741824'
        data = self.prom.custom_query(query, timeout=self.timeout)
        for i in range(len(data)):
            disks[data[i]['metric']['volume']]['all'] = data[i]['value'][1]
        return disks

    def is_network_available(self):
        query = 'up{job="windows"}'
        data = self.prom.custom_query(query)
        if len(data) != 0:
            return data[0]['value'][1]

    def _parse_metric_value(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

'''
conn = PrometheusMonitor('http://localhost:9090')
print("=== CPU ===")
print(conn.get_cpu_info())
print("=== ОЗУ ===")
print(conn.get_RAM_info())
print("=== ПЗУ ===")
print(conn.get_ROM_info())
print("=== Network ===")
print(conn.is_network_available())
'''