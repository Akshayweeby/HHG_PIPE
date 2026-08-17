# Prana frontend

Standalone frontend for the Hindi Voice RAG project. It combines the purple/lavender palette from the first reference, the calm feature presentation from the second, and the serif display typography from the third.

## Run locally

Start the existing backend on port 8000, then serve this folder:

```powershell
$py = 'C:\Users\shrad\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m http.server 5500 -d frontend
```

Open [http://127.0.0.1:5500](http://127.0.0.1:5500). Questions are sent to `http://127.0.0.1:8000/api/pipeline` on the existing backend.
