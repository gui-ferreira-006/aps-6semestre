# 📂 `database/` — Scripts de Inicialização do MySQL

Esta pasta é montada no contêiner `faca_mysql_db` em **`/docker-entrypoint-initdb.d`** (somente leitura).

## Como funciona

- Todo arquivo **`.sql`**, **`.sql.gz`** ou **`.sh`** colocado aqui é executado **automaticamente** pelo MySQL.
- A execução ocorre em **ordem alfabética** → use prefixos numéricos:
  ```
  01_schema.sql        # DDL: CREATE TABLE (usuarios, niveis_acesso, toxinas, logs_auditoria...)
  02_seed_niveis.sql   # DML: níveis de acesso 1, 2 e 3
  03_seed_usuarios.sql # DML: usuários iniciais
  04_seed_toxinas.sql  # DML: carga de toxinas
  ```
- Os scripts rodam no banco definido em `MYSQL_DATABASE` (padrão: `faca_db`), então **não é obrigatório** `USE faca_db;`.
- Salve os arquivos em **UTF-8** e, por garantia, inicie cada script com:
  ```sql
  SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```

## ⚠️ Importante: só roda no PRIMEIRO boot

Os scripts são executados **apenas quando o volume `faca_mysql_data` está vazio**.
Se você alterar/adicionar um `.sql` depois, recrie o banco do zero:

```powershell
docker compose down -v      # remove contêineres E o volume de dados (apaga o banco!)
docker compose up -d --build
```

Se algum script falhar, o contêiner do MySQL é interrompido — verifique com `docker compose logs db`.
