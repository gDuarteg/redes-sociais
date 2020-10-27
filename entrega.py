import http.client
import networkx as nx
import freeman as fm
from json import loads
from scipy import stats
from unidecode import unidecode

# https://api.rawg.io/docs/#operation/games_list

# game_nodes = {
#     id: {name: name, list: [l]},
#     id: {name: name, list: [l]},
#     id: {name: name, list: [l]}
# }

# game_edges = {
#     id: { 
#           l : peso,
#           l : peso,
#         },
#     id: { 
#           l : peso,
#           l : peso,
#         },
#     id: { 
#           l : peso,
#           l : peso,
#         },
# }

def get_rawg_api_endpoint(endpoint, conn, h) -> str:
    conn.request("GET", endpoint, headers=h)
    return loads(conn.getresponse().read())

def rawg_api_connection() -> None:
    conn = http.client.HTTPSConnection("rawg-video-games-database.p.rapidapi.com")
    headers = {
        'x-rapidapi-host': "rawg-video-games-database.p.rapidapi.com",
        'x-rapidapi-key': "c665cc5f66mshee40894946e0d28p1c5de7jsn49fab80d50ae"
        }

    return conn, headers

def gen_game_nodes(game_nodes, data, network_type) -> None:
    for game in data["results"]:
        l = []

        if network_type == 1:
            for game_tag in game["tags"]: l += [game_tag["slug"]]

        if network_type == 2:
            if game["platforms"] != None:
                for game_platform in game["platforms"]: l += [game_platform["platform"]["slug"]]
        
        # deixar vazio se platform == null?
        game_nodes[game["id"]] = { "name" : game["slug"], "list" : l }

def gen_game_edges(game_nodes, game_edges) -> None:
    for game1 in game_nodes:
        targets = {}
        
        for game2 in game_nodes:
            if game1 != game2:
                for e in game_nodes[game1]["list"]:
                    if e in game_nodes[game2]["list"] and game2 in game_edges and game1 not in game_edges[game2]:
                        if game2 in targets:
                            targets[game2] += 1
                        else: 
                            targets[game2] = 0 
        
        game_edges[game1] = targets

def build_gml(game_nodes, game_edges, network) -> None:

    with open(network, 'w') as file:
        file.write('graph [\n')
        file.write('  directed 0\n')

        for n in game_nodes.keys():
            file.write('  node [\n')
            file.write('    id {}\n'.format(n))
            file.write('    name "{}"\n'.format(unidecode(game_nodes[n]["name"])))
            file.write('  ]\n')

        for n in game_edges.keys():
            for m in game_edges[n].keys():
                file.write('  edge [\n')
                file.write('    source {}\n'.format(n))
                file.write('    target {}\n'.format(m))
                file.write('    weight {}\n'.format(game_edges[n][m]))
                file.write('  ]\n')

        file.write(']\n')

def network_nx(network):  

    g = fm.load(network)
    g.label_nodes('name')
    g.set_all_nodes(size=10, labpos='hover')
    g.draw()
    return g

def betweeness_network(network):
    bc = nx.betweenness_centrality(network)
    network.scale_nodes_size(bc)
    network.draw()

def gen_x_y(data, x1, x2, y):
    for game in data["results"]:
        lx1 = []
        lx2 = []

        for game_tag in game["tags"]: lx1 += [game_tag["slug"]]

        if game["platforms"] != None:
            for game_platform in game["platforms"]: lx2 += [game_platform["platform"]["slug"]]

        x1 += [lx1]
        x2 += [lx2]
        y += [game["rating"] + game["ratings_count"]]

def main() -> None:
    print("-------------------------------------------")

    # A. obter os dados (chamadas de API, parsing de CSV, etc.);
    
    # !: maximo de 20 jogos, talvez tenha que ser feito um for para pegar mais jogos.
    rawg_connection, rawg_headers = rawg_api_connection()
    rawg_data = get_rawg_api_endpoint(endpoint = "/games?dates=2015-03-01,2015-03-01", conn = rawg_connection, h = rawg_headers)
    
    # Rede 1: Nos: jogos; Arestas: jogos que compartilham a mesma categoria.
    # B. construir a rede (escrever GML, carregar na NetworkX);
    print("REDE 1")
    print("Nós: jogos;")
    print("Arestas: jogos que compartilham a mesma categoria;")
     
    game_nodes = {}
    game_edges = {}

    gen_game_nodes(game_nodes, rawg_data, 1)
    gen_game_edges(game_nodes, game_edges)
    build_gml(game_nodes, game_edges, 'rede1.gml')
    
    g = network_nx('rede1.gml')

    # C. calcular as métricas (chamar as funções vistas em aula ou outras);
    betweeness_network(g)

    # Rede 2: Nos: jogos; Arestas: jogos que compartilham a mesma plataforma de jogo.
    # B. construir a rede (escrever GML, carregar na NetworkX);
    print("REDE 2")
    print("Nós: jogos;")
    print("Arestas: jogos que compartilham a mesma plataforma de jogo;")
     
    game_nodes = {}
    game_edges = {}

    gen_game_nodes(game_nodes, rawg_data, 2)
    gen_game_edges(game_nodes, game_edges)
    build_gml(game_nodes, game_edges, 'rede2.gml')
    
    g = network_nx('rede2.gml')

    # C. calcular as métricas (chamar as funções vistas em aula ou outras);
    betweeness_network(g)

    # Rede 3: Nos: jogos; Arestas: jogos que compartilham mesma faixa de preco.
    # Nao foi achado dados sobre o preco dos jogos nas diferentes plataformas na api.

    # D. fazer os testes de hipótese (regressão, teste-t, etc.).
    x_tag = []
    x_platforms = []
    y_rv = []
    gen_x_y(rawg_data, x_tag, x_platforms, y_rv)

    # nao esta funcionando o teste-t
    # motivo: os x's sao uma lista que contem varias outras dentro.
    #t2, p2 = stats.ttest_ind(x_tag, y_rv)
    #print("t = " + str(t2))
    #print("p = " + str(p2))

if __name__ == "__main__":
    main()