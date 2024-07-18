## Instagram Forensic Downloader

### Descrizione

`Instagram Forensic Downloader` è uno strumento Python progettato per scaricare contenuti pubblici da profili Instagram. Utilizzando la libreria `instaloader`, questo script permette di effettuare il download di immagini, video e metadati dai post di un determinato profilo Instagram. 

### Funzionalità principali

- **Download di contenuti pubblici**: Scarica foto, video e metadati dai post pubblici di un profilo Instagram specificato.
- **Calcolo hash MD5**: Calcola e salva gli hash MD5 per verificare l'integrità dei file scaricati.
- **Conversione JSON a TXT**: Converte i file JSON dei metadati in file TXT per una lettura più facile.
- **Registrazione delle operazioni**: Crea un file di log per tracciare tutte le operazioni eseguite durante il processo di download.

### Utilizzo

1. **Inserisci l'URL del profilo Instagram pubblico**: Fornisci l'URL del profilo Instagram da cui desideri scaricare i contenuti.
2. **Scaricamento e salvataggio**: I contenuti verranno scaricati in una directory creata con il nome del profilo nella stessa cartella dove si trova lo script.
3. **Calcolo e salvataggio hash MD5**: Gli hash MD5 dei file scaricati vengono calcolati e salvati in un file `hash.txt` nella directory del profilo.
4. **Log delle operazioni**: Un file di log viene creato per tracciare tutte le operazioni eseguite durante il processo di download.

### Requisiti

- Python 3.6 o superiore
- `instaloader` library
- `hashlib` library
- `json` library
- `logging` library
- `shutil` library

### Installazione

1. Clona questo repository:

    ```sh
    git clone https://github.com/tuo_username/instagram_forensic_downloader.git
    ```

2. Installa le dipendenze:

    ```sh
    pip install instaloader
    ```

### Esecuzione dello script

Per eseguire lo script, utilizza il seguente comando:

```sh
python instagram_forensic_downloader.py
```

### Esempio di utilizzo

Quando esegui lo script, ti verrà richiesto di inserire l'URL del profilo Instagram pubblico:

```sh
Enter the public Instagram profile URL: https://www.instagram.com/username/
```

Lo script procederà a scaricare i contenuti del profilo specificato e li salverà in una directory con il nome del profilo nella stessa cartella dove si trova lo script.

### Note

- Questo strumento è destinato esclusivamente per il download di contenuti pubblici e non può accedere a contenuti privati.
- Assicurati di rispettare i termini di servizio di Instagram durante l'utilizzo di questo strumento.

### Contribuzione

Le contribuzioni sono benvenute! Se desideri contribuire, apri una issue o invia una pull request.

### Licenza

Questo progetto è distribuito sotto la licenza MIT. Vedi il file `LICENSE` per maggiori dettagli.

