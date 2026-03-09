# 🚀 Hostinger VPS Deployment Guide - Lead Scraper System

Complete guide to deploy the Lead Scraper System on Hostinger VPS with Streamlit, MongoDB Atlas, and process management.

---

## 📋 Prerequisites

### What You Need:
1. **Hostinger VPS** (minimum: 2GB RAM, 2 CPU cores recommended)
2. **Domain name** (optional but recommended)
3. **MongoDB Atlas account** (free tier works)
4. **API Keys** ready:
   - OpenRouter API key
   - Hunter.io API key
   - Apify API key
   - Perplexity API key
   - ContactOut API key (optional)

---

## 🔧 Part 1: VPS Initial Setup

### Step 1: Connect to Your VPS

```bash
# From your local machine (PowerShell/Terminal)
ssh root@your-vps-ip
# Enter your password when prompted
```

### Step 2: Update System & Install Dependencies

```bash
# Update package list
apt update && apt upgrade -y

# Install Python 3.10+ and essential tools
apt install python3 python3-pip python3-venv git nginx supervisor -y

# Verify Python version (should be 3.10+)
python3 --version
```

### Step 3: Create Application User (Security Best Practice)

```bash
# Create a dedicated user for the app
adduser hustlehouse --disabled-password --gecos ""

# Add to sudo group (optional)
usermod -aG sudo hustlehouse

# Switch to the new user
su - hustlehouse
```

---

## 📦 Part 2: Deploy Application

### Step 1: Clone Repository

```bash
# Clone your repository
cd ~
git clone https://github.com/thhteamspace/Hustle-Leadscrapper.git
cd Hustle-Leadscrapper

# Or upload files via SFTP if not using Git
```

### Step 2: Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

```bash
# Create .env file
nano .env
```

**Paste your configuration:**

```env
# API Keys
OPENROUTER_API_KEY=your_openrouter_key_here
HUNTER_API_KEY=your_hunter_api_key_here
APIFY_API_KEY=your_apify_api_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here
CONTACTOUT_API_KEY=your_contactout_key_here

# MongoDB Atlas
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/leadscraper?retryWrites=true&w=majority

# OpenRouter Configuration
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Application Settings
LOG_LEVEL=INFO
```

**Save and exit:** Press `Ctrl+X`, then `Y`, then `Enter`

### Step 4: Test Application Locally

```bash
# Test that everything works
streamlit run app.py --server.port 8501

# Press Ctrl+C to stop after testing
```

---

## 🔄 Part 3: Process Management with Supervisor

Supervisor keeps your Streamlit app running 24/7, auto-restarts on crashes.

### Step 1: Create Supervisor Configuration

```bash
# Switch back to root
exit  # Exit from hustlehouse user

# Create supervisor config
nano /etc/supervisor/conf.d/leadscraper.conf
```

**Paste this configuration:**

```ini
[program:leadscraper]
command=/home/hustlehouse/Hustle-Leadscrapper/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
directory=/home/hustlehouse/Hustle-Leadscrapper
user=hustlehouse
autostart=true
autorestart=true
startretries=3
stderr_logfile=/var/log/leadscraper.err.log
stdout_logfile=/var/log/leadscraper.out.log
environment=HOME="/home/hustlehouse",USER="hustlehouse"
```

**Save and exit:** `Ctrl+X`, `Y`, `Enter`

### Step 2: Start Supervisor

```bash
# Update supervisor
supervisorctl reread
supervisorctl update

# Start the application
supervisorctl start leadscraper

# Check status
supervisorctl status leadscraper
```

**Expected output:** `leadscraper RUNNING`

### Step 3: Supervisor Management Commands

```bash
# View logs
tail -f /var/log/leadscraper.out.log
tail -f /var/log/leadscraper.err.log

# Restart app
supervisorctl restart leadscraper

# Stop app
supervisorctl stop leadscraper

# Start app
supervisorctl start leadscraper
```

---

## 🌐 Part 4: Nginx Reverse Proxy Setup

### Option A: Access via IP Address (Simple)

```bash
# Create Nginx config
nano /etc/nginx/sites-available/leadscraper
```

**Paste this:**

```nginx
server {
    listen 80;
    server_name your-vps-ip;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### Option B: Access via Domain Name (Recommended)

```bash
nano /etc/nginx/sites-available/leadscraper
```

**Paste this:**

```nginx
server {
    listen 80;
    server_name leads.yourdomain.com;  # Change to your domain

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### Enable Nginx Site

```bash
# Create symbolic link
ln -s /etc/nginx/sites-available/leadscraper /etc/nginx/sites-enabled/

# Remove default site
rm /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Restart Nginx
systemctl restart nginx
```

---

## 🔒 Part 5: SSL Certificate (HTTPS) - Optional but Recommended

### Install Certbot

```bash
# Install Certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate (replace with your domain)
certbot --nginx -d leads.yourdomain.com

# Follow prompts:
# - Enter email address
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)
```

**Your site is now accessible at:** `https://leads.yourdomain.com`

### Auto-Renewal Setup

```bash
# Test auto-renewal
certbot renew --dry-run

# Certbot automatically sets up auto-renewal
```

---

## 🔥 Part 6: Firewall Configuration

```bash
# Install UFW (if not installed)
apt install ufw -y

# Allow SSH (IMPORTANT - do this first!)
ufw allow 22/tcp

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

---

## 📊 Part 7: MongoDB Atlas Setup

### Create MongoDB Atlas Cluster

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free cluster
3. Create database user
4. Whitelist VPS IP address:
   - Go to **Network Access**
   - Click **Add IP Address**
   - Enter your VPS IP or use `0.0.0.0/0` (allow all)

### Get Connection String

```
mongodb+srv://username:password@cluster.mongodb.net/leadscraper?retryWrites=true&w=majority
```

Add this to your `.env` file as `MONGODB_URI`

---

## 🔄 Part 8: Deployment Workflow

### Initial Deployment

```bash
# As root
su - hustlehouse
cd ~/Hustle-Leadscrapper
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
exit

# Restart app
supervisorctl restart leadscraper
```

### Future Updates

Create a deployment script:

```bash
# As hustlehouse user
nano ~/deploy.sh
```

**Paste this:**

```bash
#!/bin/bash
cd ~/Hustle-Leadscrapper
git pull origin main
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo supervisorctl restart leadscraper
echo "✅ Deployment complete!"
```

**Make executable:**

```bash
chmod +x ~/deploy.sh
```

**To deploy updates:**

```bash
~/deploy.sh
```

---

## 🔍 Part 9: Monitoring & Troubleshooting

### View Application Logs

```bash
# Real-time logs
tail -f /var/log/leadscraper.out.log

# Error logs
tail -f /var/log/leadscraper.err.log

# Last 100 lines
tail -n 100 /var/log/leadscraper.out.log
```

### Check Application Status

```bash
# Supervisor status
supervisorctl status

# Nginx status
systemctl status nginx

# Check if app is listening
netstat -tulpn | grep 8501
```

### Common Issues

**1. App not starting:**
```bash
# Check logs
tail -f /var/log/leadscraper.err.log

# Check Python errors
cd /home/hustlehouse/Hustle-Leadscrapper
source venv/bin/activate
python app.py
```

**2. Can't access via browser:**
```bash
# Check Nginx
nginx -t
systemctl status nginx

# Check firewall
ufw status
```

**3. MongoDB connection failed:**
```bash
# Test connection
cd /home/hustlehouse/Hustle-Leadscrapper
source venv/bin/activate
python -c "from backend.database_mongodb import MongoDBManager; db = MongoDBManager(); print('Connected!')"
```

### Performance Monitoring

```bash
# Check CPU/Memory usage
htop

# Check disk space
df -h

# Check app resource usage
ps aux | grep streamlit
```

---

## 🎯 Part 10: Access Your Application

### Via IP Address:
```
http://your-vps-ip
```

### Via Domain (with SSL):
```
https://leads.yourdomain.com
```

---

## 🔐 Part 11: Security Hardening (Recommended)

### 1. Change SSH Port

```bash
nano /etc/ssh/sshd_config
# Change Port 22 to Port 2222
systemctl restart sshd

# Update firewall
ufw allow 2222/tcp
ufw delete allow 22/tcp
```

### 2. Disable Root Login

```bash
nano /etc/ssh/sshd_config
# Change PermitRootLogin yes to PermitRootLogin no
systemctl restart sshd
```

### 3. Add Basic Authentication (Optional)

Create password protection for Streamlit:

```bash
# Install apache2-utils
apt install apache2-utils

# Create password file
htpasswd -c /etc/nginx/.htpasswd admin
# Enter password when prompted
```

**Update Nginx config:**

```nginx
location / {
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    proxy_pass http://localhost:8501;
    # ... rest of config
}
```

```bash
# Restart Nginx
systemctl restart nginx
```

---

## 🔄 Part 12: Backup Strategy

### Automatic Backup Script

```bash
nano ~/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/hustlehouse/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup application
tar -czf $BACKUP_DIR/leadscraper_$DATE.tar.gz \
    /home/hustlehouse/Hustle-Leadscrapper \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='.git'

# Keep only last 7 backups
cd $BACKUP_DIR
ls -t | tail -n +8 | xargs rm -f

echo "✅ Backup completed: leadscraper_$DATE.tar.gz"
```

```bash
chmod +x ~/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/hustlehouse/backup.sh
```

---

## 📱 Quick Reference Commands

```bash
# Restart application
sudo supervisorctl restart leadscraper

# View logs
tail -f /var/log/leadscraper.out.log

# Update application
cd ~/Hustle-Leadscrapper && git pull && sudo supervisorctl restart leadscraper

# Check status
sudo supervisorctl status
sudo systemctl status nginx

# Restart Nginx
sudo systemctl restart nginx

# Check firewall
sudo ufw status
```

---

## 🆘 Support Checklist

If something goes wrong, check:

- [ ] Supervisor is running: `supervisorctl status`
- [ ] Nginx is running: `systemctl status nginx`
- [ ] Port 8501 is listening: `netstat -tulpn | grep 8501`
- [ ] Firewall allows traffic: `ufw status`
- [ ] MongoDB connection works
- [ ] .env file has correct API keys
- [ ] Check error logs: `/var/log/leadscraper.err.log`

---

## 🎉 Congratulations!

Your Lead Scraper System is now deployed on Hostinger VPS and accessible 24/7!

**Next Steps:**
1. Test all scraping features
2. Monitor logs for first few hours
3. Set up regular backups
4. Share access URL with your team

**Need help?** Check the logs or contact support.
