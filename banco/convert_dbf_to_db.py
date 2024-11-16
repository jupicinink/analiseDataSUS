import csv
import os
import duckdb
import time
import pandas as pd
from dbfread import DBF

# Diretório dos arquivos em DBF
dbf_directory = "./banco/"
aux_directory = "./banco/"
# Diretório onde vai ficar a base de dados
output_directory = "./database/"    
sql_creation_file_location = "./banco/database_creation.sql"
# Nome da tabela principal
table_name = "dadosacidentetrabalho"
# Nome do arquivo da Database
database_name = "database_cd"


# Caso o arquivo exista, deleta ele
if os.path.exists(f"{output_directory}/{database_name}.db"):
    os.remove(f"{output_directory}/{database_name}.db")
# caso o diretório nao exista, cria ele
if not os.path.exists(output_directory):
    os.mkdir(output_directory) 

# Cria a base de dados
database = duckdb.connect(f"{output_directory}/{database_name}.db") 

# Lista o nome dos arquivos DBF na pasta
dbf_db_files = []
dbf_db_files = [f for f in os.listdir(dbf_directory) if f.lower().endswith('.dbf')]
# Lista o nome dos arquivos CSV na pasta auxiliar
aux_db_files = []
#aux_db_files = [f for f in os.listdir(aux_directory) if f.lower().endswith('.csv')]

# Contador pra ver quantos arquivos foram convertidos
counter = 0
# Tempo inicial para pegar o tempo total que ficou convertendo e importando
total_time = time.time()
# Itera por todos os arquivos CSV
for csv_name in aux_db_files:
    counter += 1
    # pega o nome do arquivo sem extensão
    name = csv_name[:-4]
    # cria a tabela para o cnv que é um csv agora, e coloca o Código como chave primária
    database.sql(f"CREATE TABLE {name.lower()} (ID integer, descricao TEXT, Codigo Text, Primary Key (Codigo));")
    # Importa os dados pra dentro da tabela
    database.sql(f"INSERT INTO {name.lower()} SELECT * FROM read_csv('{aux_directory}{csv_name}');")
    print(f"\r{counter}/{len(aux_db_files)} {round((counter/len(aux_db_files))*100, 2)}%",end="",)
print(f"\nTempo total para inserção de todas os dados no BD {round(time.time() - total_time, 2)} segundos")

aux_db_files = []
#aux_db_files = [f for f in os.listdir(aux_directory) if f.lower().endswith('.dbf')]

# Contador pra ver quantos arquivos foram convertidosKubernetes é um sistema de orquestração de contêineres open-source que automatiza a implantação, o dimensionamento e a gestão de aplicações em contêineres. Ele foi originalmente projetado pelo Google e agora é mantido pela Cloud Native Computing Foundation. Wikipédia
counter = 0
# Tempo inicial para pegar o tempo total que ficou convertendo e importando
total_time = time.time()

for csv_name in aux_db_files:
    counter += 1
    # pega o nome do arquivo sem extensão
    name = csv_name[:-4]
    table = DBF(f'{aux_directory}{csv_name}', 'latin-1')
    csv_path = f"{output_directory}/{name}.csv"
    # Abre um CSV e joga todo as coisas do DBF para o CSV
    with open(csv_path, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(table.field_names)
        for record in table:
            writer.writerow(list(record.values()))
    # cria a tabela para o cnv que é um csv agora, e coloca o Código como chave primária
    database.sql(f"CREATE TABLE {name.lower()} AS FROM read_csv('{output_directory}{name}.csv');")
    # Importa os dados pra dentro da tabela
    # database.sql(f"INSERT INTO {name.lower()} SELECT * FROM read_csv('{output_directory}{name}.csv');")
    print(f"\r{counter}/{len(aux_db_files)} {round((counter/len(aux_db_files))*100, 2)}%",end="",)
    os.remove(csv_path)
print(f"\nTempo total para inserção de todas os dados no BD {round(time.time() - total_time, 2)} segundos")

# Abre o arquivo SQL da criação da tabela principal dos DBFs
fd = open(sql_creation_file_location, 'r')
# Cospe todo o arquivo na variavel
sqlFile = fd.read()
# fecha o arquivo ufa
fd.close()

# Cria a base no banco
database.execute(sqlFile)

# Contador pra ver quantos arquivos foram convertidos
counter = 0
# Tempo inicial para pegar o tempo total que ficou convertendo e importando
total_time = time.time()
for dbf_name in dbf_db_files:
    start_time = time.time()
    counter += 1
    # Abre o DBF e joga pra um arquivo
    table = DBF(f'{dbf_directory}/{dbf_name}', 'latin-1')
    csv_path = f"{output_directory}/{table.name}.csv"
    # Abre um CSV e joga todo as coisas do DBF para o CSV
    with open(csv_path, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(table.field_names)
        for record in table:
            writer.writerow(list(record.values()))
    # Retorna as colunas da tabela no banco de dados
    columns = database.query(f"PRAGMA table_info({table_name});").fetchall()
    # Cria uma String com os nomes das colunas para a inserção no banco de dados
    columns = ", ".join([i[1] for i in columns])
    # Insere os dados no banco de dados, utilizando somente as colunas listadas
    database.sql(f"INSERT INTO {table_name}({columns}) SELECT {columns} FROM read_csv('{output_directory}/{table.name}.csv');")
    # Deleta o arquivo CSV criado
    os.remove(csv_path)
    # Mostra o progresso
    print(f"\r{counter}/{len(dbf_db_files)} {round((counter/len(dbf_db_files))*100, 2)}%   ----  Tempo demorado no ultimo arquivo: {round(time.time() - start_time, 2)} segundos",end="",)
# Adicionado todos os DBFs na tabela

# Mostra o tempo total de importação
total_time = time.time() - total_time
total_time = f"{round(total_time, 2)} segundos" if total_time < 60 else f"{round(total_time/60, 2)} minutos"
print(f"\nTempo total para inserção de todas os dados no BD {total_time}")
