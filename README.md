# Exercice de Data Engineer, PREDICTICE


Ce projet a pour but de démontrer mes compétences en extraction de données à partir d'un site web.

L'objectif principal est de collecter des données de jurisprudences provenant du site https://www.legifrance.gouv.fr/

## Objectifs du projet

Les objectifs de ce projet sont les suivants :
1. Scrapper les jurisprudences du site web de [legifrance](https://www.legifrance.gouv.fr/).
2. Extraire les données pertinentes et de les enregistrer au format JSON.
3. Stocker les données récoltées dans un fichier parquet.
4. Remplacer les noms anonymisés par leurs équivalents non anonymisés.
5. Exportez les données transformées dans un index ElasticSearch.
6. Emballez l'ensemble du processus dans un conteneur.

## Technologies utilisées

Ce projet utilise les technologies suivantes :
* Python
* Bibliothèques Python : Utilisation de Selenium pour permettre de scrapper le site web sans être bloqué par l'anti-bot.
* ElasticSearch
* Docker

## Notes
* Pour mes premiers tests de scrapping, j'ai essayé de faire au plus simple, et d'utiliser request pour récupérer les données.
* Le souci de cette méthode est qu'il arrive parfois que certaines pages soient inaccessibles. En effet, le site est protégé par un système d'anti-bots **Imperva Incapsula**, et request.get ne permet pas de toujours l'éviter.
* Il a donc fallu trouver une solution qui fonctionne à chaque exécution et sans perdre de données. C'est pourquoi j'utilise Selenium pour récupérer le code source des pages du site.
* Bien que cela ralentisse beaucoup l'exécution du scrapper, je trouve que 6 minutes d'exécution reste raisonnable.

## Procedure de lancement
Le projet étant conteneurisé via docker, il est nécessaire de lancer un docker-compose afin d'installer les librairies python et de lancer l'application.
```shell
docker-compose up --build -d
```
Après build du projet, vous pouvez visualiser les logs
```shell
docker-compose logs -f app
```

Afin de visualiser les données dans ElasticSearch, rendez-vous sur [Kibana](http://localhost:5601/app/dev_tools#/console).
Pour visualiser toutes les données présentes dans l'index :
```sql
GET jurisprudence/_search
{
  "query": {
    "match_all": {}
  }
}
```

Enfin, vous trouverez le fichier parquet d'output dans le dossier output.

## Auteur 
Tom PAYET.
