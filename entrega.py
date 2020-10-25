
# https://api.rawg.io/docs/#operation/games_list
#
# Objetivo deste código: nós são artistas e arestas são baseadas
# na API de "related artists". Como não há tempo de baixar todos
# os artistas do Spotify inteiro, partimos de uma "raiz" inicial
# e fazemos uma "bola de neve" a partir dessa raiz com recursão.
# Ou seja, pegamos a raiz (0 níveis), os vizinhos da raiz (1 nível),
# os vizinhos dos vizinhos da raiz (2 níveis) e assim em diante.

def get_rawg_api_endpoint(endpoint, conn, h) -> str:
    import json
    conn.request("GET", endpoint, headers=h)
    return json.loads(conn.getresponse().read())

def rawg_api_connection() -> None:
    import http.client
    conn = http.client.HTTPSConnection("rawg-video-games-database.p.rapidapi.com")
    headers = {
        'x-rapidapi-host': "rawg-video-games-database.p.rapidapi.com",
        'x-rapidapi-key': "c665cc5f66mshee40894946e0d28p1c5de7jsn49fab80d50ae"
        }

    return conn, headers

def gen_game_names(game_names, data) -> None:
    for game in data["results"]:
        tags = []

        for game_tag in game["tags"]: tags += [game_tag["slug"]]

        game_names[game["id"]] = { "name" : game["slug"], "tags" : tags }
        
def gen_game_same_cat(game_names, game_same_cat) -> None:
    for game1 in game_names:
        targets = []
        
        for game2 in game_names:
            if game1 != game2:
                for tag in game_names[game1]["tags"]:
                    if tag in game_names[game2]["tags"]:
                        targets += [game2] 
        
        game_same_cat[game1] = targets

def build_gml(game_names, game_same_cat) -> None:
    from unidecode import unidecode

    with open('jogo.gml', 'w') as file:
        file.write('graph [\n')
        file.write('  directed 0\n')

        for n in game_names.keys():
            file.write('  node [\n')
            file.write('    id "{}"\n'.format(n))
            file.write('    name "{}"\n'.format(unidecode(game_names[n]["name"])))
            file.write('  ]\n')

        for n in game_same_cat.keys():
            for m in game_same_cat[n]:
                file.write('  edge [\n')
                file.write('    source "{}"\n'.format(n))
                file.write('    target "{}"\n'.format(m))
                file.write('  ]\n')

        file.write(']\n')

def network_nx():  
    import networkx as nx
    import freeman as fm

    g = fm.load('jogo.gml')
    g.label_nodes('name')
    g.set_all_nodes(size=10, labpos='hover')
    g.draw()

def main() -> None:
    print("-------------------------------------------")

    # A. obter os dados (chamadas de API, parsing de CSV, etc.);
    # !: maximo de 20 jogos, talvez tenha que ser feito um for para pegar mais jogos.
    rawg_connection, rawg_headers = rawg_api_connection()
    rawg_data = get_rawg_api_endpoint(endpoint = "/games?dates=2015-01-01,2015-01-01", conn = rawg_connection, h = rawg_headers)

    # B. construir a rede (escrever GML, carregar na NetworkX);
    game_names = {}
    game_same_cat = {}

    gen_game_names(game_names, rawg_data)
    gen_game_same_cat(game_names, game_same_cat)
    build_gml(game_names, game_same_cat)

    network_nx()
    # C. calcular as métricas (chamar as funções vistas em aula ou outras);

    # D. fazer os testes de hipótese (regressão, teste-t, etc.).

if __name__ == "__main__":
    main()
    