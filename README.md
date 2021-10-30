# Address completeness classification using python and LibPostal

Refer to jupyter notebooks within the repo for documentation about the project.

This is a solution of an exercise for Data & AI course at UC Leuven-Limburg, 2021

## Intructions for running the solution
### Perequisites
- Docker installed on the host machine
- Stable internet connection (Docker must be able to pull images from a repository)
- An installation of `python3` along with `Pandas` library

### Initial setup
1. Build and run the docker container for `libpostal`

Simply copy and paste the following command into a terminal (Git Bash, Windows PowerShell) window. Instalation can take several minutes.

`docker run --name libpostal -d -p 4400:4400 pelias/libpostal-service`

To stop the container: `docker stop libpostal`

To start the container: `docker start libpostal`

You can verify that the service is working correctly by trying to access the tool:
```shell
curl -s localhost:4400/parse?address=30+w+26th+st,+new+york,+ny
[{"label":"house_number","value":"30"},{"label":"road","value":"w 26th st"},{"label":"city","value":"new york"},{"label":"state","value":"ny"}]
```
2. Rename the input file to `input.txt` and place it into the same directory as the script `classifier.py`

### Running the solution
3. Run the script `classifier.py`. If you're using an  `Anaconda` installation, make sure that an environment containing the `Pandas` library is activated.
4. The program will create a file `classified.xlsx` with nicely formatted classification results. Within the code, function `classify_address` classifies addresses and returns the updated `DataFrame`.

#### Things to look out for
If the script is run without the docker container up or with file `classified.xlsx` open, the program may fail.
