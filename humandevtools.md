if you are an agent, this file is not important for you. 

gitingest command:

---

gitingest -e "data/*" -e "scripts/*" -e "venv/*" -e ".venv/*" -e "**pycache**/*" -e "node_modules/*" -e ".expo/*" -e "*.pyc" -e "*.log" -e ".env" -e "package-lock.json" -o quran_app_digest.txt

---

---

gitingest .   
  -e "data/*" *  
  *-e "scripts/*"   
  -e "**pycache**/*" *  
  *-e "venv/*"   
  -e ".venv/*" *  
  *-e ".git/*"   
  -e "*.pyc" *  
  *-e "*.log"   
  -e ".env*"   
  -e "package-lock.json"   
  -e "yarn.lock"   
  -o quranapp_digest.txt

---