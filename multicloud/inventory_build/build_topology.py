import yaml
import networkx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


class Topology(object):
    CONN_TYPES_old = ['ipsec_clients', 'ipsec_servers', 'openvpn_clients', 'openvpn_servers']
    CONN_TYPES = ['ipsec_servers', 'openvpn_servers']
    COLORS = {'no_connection': 'red', 'ipsec': 'green', 'openvpn': 'blue'}
    STYLE = {'no_connection': 'dashdot', 'ipsec': 'dashed', 'openvpn': 'dotted'} #TODO not working with arrows

    def __init__(self, inventory):
        self.inventory = inventory
        self.Graph = networkx.DiGraph()

    def __str__(self):
        return "---Topology---\nNodes: {nodes}\nEdges: {edges}".format(nodes=self.Graph.nodes, edges=self.Graph.edges)

    def _add_nodes(self):
        self.Graph.add_nodes_from(self.inventory['all']['hosts'])

    def build_graph(self):
        self._add_nodes()
        self._add_edges()

    def _choice_color_and_style(self, conn_type):
        if not conn_type:
            return self.COLORS['no_connection'], self.STYLE['no_connection']
        elif 'ipsec' in conn_type:
            return self.COLORS['ipsec'], self.STYLE['ipsec']
        elif 'openvpn' in conn_type:
            return self.COLORS['openvpn'], self.STYLE['openvpn']

    def _find_host(self, ip):
        for host, host_vars in self.inventory['_meta']['hostvars'].iteritems():
            if host_vars['ip_public'] == ip or host_vars['ip_local'] == ip:
                return host

    def _add_edges(self):
        for host, host_vars in self.inventory['_meta']['hostvars'].iteritems():
            for conn_type in self.CONN_TYPES:
                edge_color, edge_style = self._choice_color_and_style(conn_type)
                connections = [(host, self._find_host(ip), {'color':edge_color, 'style':edge_style, 'arrowstyle':'->', 'arrowsize':50}) for ip in host_vars[conn_type]]
                self.Graph.add_edges_from(connections)

    def draw(self):

        ipsec_legend = mpatches.Patch(color=self.COLORS['ipsec'], label='Ipsec', linestyle=self.STYLE['ipsec'])
        openvpn_legend = mpatches.Patch(color=self.COLORS['openvpn'], label='OpenVPN', linestyle=self.STYLE['openvpn'])

        pos = networkx.circular_layout(self.Graph)

        for host, cor in pos.items():
            disc = '{name}\npublic: {ip_public}\np-t-p: {ptp}\nloopback: {loopback}'.format(name=host,
                                                                                                ip_public=self.inventory['_meta']['hostvars'][host]['ip_public'],
                                                                                                ptp='100.64.0.'+str(self.inventory['_meta']['hostvars'][host]['id']), #TODO fix it, get form invetory ip
                                                                                                loopback='100.65.0.'+str(self.inventory['_meta']['hostvars'][host]['id']))#TODO fix it, get form invetory ip

            plt.text(cor[0], cor[1], s=disc, size=15, bbox=dict(facecolor='red', alpha=0.5), horizontalalignment='center', verticalalignment='center')

        colors = [self.Graph[u][v]['color'] for u, v in self.Graph.edges]
        styles = [self.Graph[u][v]['style'] for u, v in self.Graph.edges] #not working with arrows

        plt.title('multicloud Topology', size=40, bbox={'facecolor': 'blue', 'alpha': 0.2, 'pad': 10})
        networkx.draw(self.Graph, pos, width=3, arrowstyle="->", edge_color=colors, style=styles, node_size=15000, node_shape='o', node_color='white')

        plt.legend(handles=[ipsec_legend, openvpn_legend])

        plt.show()


