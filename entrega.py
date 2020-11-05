import http.client
import networkx as nx
import freeman as fm
from json import loads, dump
from scipy import stats
from unidecode import unidecode
import pandas as pd
import seaborn as sns
import statsmodels.api as sm
import matplotlib.pyplot as plt

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

def gen_data(conn, h, review_threshold = 250, month = [1, 12], day = [1, 31], year = 2015) -> None:
    rawg_data = {"results":[]}
    game_found_debug = 0

    for j in range(month[0], month[1] + 1):
        for i in range(day[0], day[1] + 1):
            page = 1
            response_count = 0
            response = {"count": None}

            while (response_count != response["count"]):
                query = "/games?page_size=40&page={}&dates={}-{:02d}-{:02d},{}-{:02d}-{:02d}".format(page, year, j, i, year, j, i)
                response = get_rawg_api_endpoint(endpoint=query, conn=conn, h=h)
                response_count += len(response["results"])
                print()
                print(query)

                for game in response['results']:
                    if game["ratings_count"] > review_threshold and game["slug"] not in rawg_data.keys():
                        rawg_data["results"] += [game]
                        game_found_debug += 1

                page += 1

    with open('aa.json', 'w') as file:
            dump(rawg_data, file)

    print(game_found_debug)

def gen_game_nodes(game_nodes, data, network_type) -> None:
    for game in data["results"]:
        l = []

        if network_type == 1:
            for game_tag in game["tags"]: l += [game_tag["slug"]]

        if network_type == 2:
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

def build_gml(game_nodes, game_edges, network, weight_list) -> None:

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
                weight_list += [game_edges[n][m]]

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

def degree_network(network):
    dc = nx.degree_centrality(network)
    network.scale_nodes_size(dc)
    network.draw()

def gen_x_y(data, x1, x2, y):
    for game in data["results"]:
        lx1 = []
        lx2 = []

        for game_tag in game["tags"]: lx1 += [game_tag["slug"]]

        for game_platform in game["platforms"]: lx2 += [game_platform["platform"]["slug"]]

        x1 += [lx1]
        x2 += [lx2]
        y += [game["rating"]]

def unique(lst):
    l = []

    for lis in lst:
        for category in lis:
            if category not in l:
                l += [category]
    
    return l

def one_hot_encoding(element, lists):
    one_hot_list = []
    for lis in lists:
        if element in lis: one_hot_list += [1]
        else: one_hot_list += [0]

    return one_hot_list

def gen_df(x_tag, x_platforms, y_rv):
    x_tag_unique = unique(x_tag)
    d = {"ratings" : y_rv}
    
    for category in x_tag_unique:
        d[category] = one_hot_encoding(category, x_tag)
        
    return pd.DataFrame(data=d)

def gen_nw_1(rawg_data, weight_nw_1):
    # Rede 1: Nos: jogos; Arestas: jogos que compartilham a mesma categoria.
    print("REDE 1")
    print("Nós: jogos;")
    print("Arestas: jogos que compartilham a mesma categoria;")
     
    game_nodes = {}
    game_edges = {}

    gen_game_nodes(game_nodes, rawg_data, 1)
    gen_game_edges(game_nodes, game_edges)
    build_gml(game_nodes, game_edges, 'rede1.gml', weight_nw_1)
    
    g = network_nx('rede1.gml')

    # C. calcular as métricas (chamar as funções vistas em aula ou outras);
    betweeness_network(g)
    degree_network(g)

    return g

def gen_nw_2(rawg_data, weight_nw_2):
    # Rede 2: Nos: jogos; Arestas: jogos que compartilham a mesma plataforma de jogo.
    print("REDE 2")
    print("Nós: jogos;")
    print("Arestas: jogos que compartilham a mesma plataforma de jogo;")
     
    game_nodes = {}
    game_edges = {}

    gen_game_nodes(game_nodes, rawg_data, 2)
    gen_game_edges(game_nodes, game_edges)
    build_gml(game_nodes, game_edges, 'rede2.gml', weight_nw_2)
    
    g = network_nx('rede2.gml')

    # C. calcular as métricas (chamar as funções vistas em aula ou outras);
    betweeness_network(g)
    degree_network(g)

    return g

def main() -> None:
    # A. obter os dados (chamadas de API, parsing de CSV, etc.);

    rawg_connection, rawg_headers = rawg_api_connection()
    gen_data(rawg_connection, rawg_headers)

    with open('aa.json', 'r') as file: rawg_data = loads(file.read())

    # B. construir a rede (escrever GML, carregar na NetworkX);
    weight_nw_1 = []
    g = gen_nw_1(rawg_data, weight_nw_1)
    plt.hist(weight_nw_1, bins=13, alpha=0.5)
    plt.title('Weight data for network 1')
    # weight_nw_2 = []
    # g = gen_nw_2(rawg_data, weight_nw_2)

    # D. fazer os testes de hipótese (regressão, teste-t, etc.).
    x_tag = []
    x_platforms = []
    y_rv = []
    gen_x_y(rawg_data, x_tag, x_platforms, y_rv)
    df = gen_df(x_tag, x_platforms, y_rv)

    for category in df:
        if category != 'ratings':
            print()
            print(category)
            print()
            model = sm.OLS(df['ratings'], df[category])
            result = model.fit()
            print(result.summary())
            print()

if __name__ == "__main__":
    main()