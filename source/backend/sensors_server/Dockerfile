# 1. Usa una versione di Python leggera e ufficiale
FROM python:3.10-slim

# 2. Crea una cartella virtuale dentro il container chiamata /app
WORKDIR /app

# 3. Copia il file delle dipendenze e installale
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copia tutto il resto del tuo codice (il main.py) dentro il container
COPY . .

# 5. Il comando da lanciare quando il container si accende
CMD ["python", "-u", "main.py"]