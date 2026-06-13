# Deploying to PythonAnywhere Guide

This guide walks you through the step-by-step process of deploying the **Iskolearn Web App** to PythonAnywhere.

---

## Step 1: Upload Your Code to PythonAnywhere

You have two main options to upload your project files:

### Option A: Using Git (Recommended)
1. Push your project code to a remote repository (e.g., GitHub, GitLab).
2. Open a **Bash Console** on PythonAnywhere.
3. Clone your repository:
   ```bash
   git clone https://github.com/YOUR_GITHUB_USERNAME/iskolearn_webapp.git
   ```

### Option B: Uploading a ZIP file
1. Compress your project folder into a ZIP file (excluding `.venv`, `.vscode`, and `__pycache__` folders).
2. Go to the **Files** tab on PythonAnywhere.
3. Upload the ZIP file to your home directory (`/home/YOUR_USERNAME/`).
4. Open a **Bash Console** on PythonAnywhere and extract the file:
   ```bash
   unzip iskolearn_webapp.zip -d ~/iskolearn_webapp
   ```

---

## Step 2: Create a Virtual Environment and Install Dependencies

1. In the PythonAnywhere **Bash Console**, create a Python 3.10 virtual environment:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 iskolearn-venv
   ```
   *Note: This will automatically activate the virtual environment.*

2. Navigate to your project directory:
   ```bash
   cd ~/iskolearn_webapp
   ```

3. Install the application dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Step 3: Configure the Web App on PythonAnywhere

1. Go to the **Web** tab in the PythonAnywhere dashboard.
2. Click **Add a new web app**.
3. Choose **Manual Configuration** (Do NOT choose "Flask" as manual configuration gives you complete control over paths and virtual environments).
4. Select **Python 3.10** (or whichever version you used for the virtual environment).
5. Finish the setup wizard.

---

## Step 4: Configure Paths in the Web Tab

Under the newly created web app settings on the **Web** tab, configure the following sections:

### 1. Code Section
* **Source code**: `/home/YOUR_USERNAME/iskolearn_webapp`
* **Working directory**: `/home/YOUR_USERNAME/iskolearn_webapp`

### 2. Virtualenv Section
* **Virtualenv**: `/home/YOUR_USERNAME/.virtualenvs/iskolearn-venv`

---

## Step 5: Configure the WSGI File

1. In the **Code** section of the Web tab, click on the **WSGI configuration file** link (it looks like `/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py`).
2. Delete all existing content in that file.
3. Add the following configuration (replace `YOUR_USERNAME` with your actual PythonAnywhere username):
   ```python
   import sys

   # Add your project directory to the sys.path
   project_home = '/home/YOUR_USERNAME/iskolearn_webapp'
   if project_home not in sys.path:
       sys.path = [project_home] + sys.path

   # Import the flask app object defined in wsgi.py
   from wsgi import application
   ```
4. Click **Save** in the top right.

---

## Step 6: Configure Static Files

To make PythonAnywhere serve CSS, JS, and images directly (which is much faster and standard for production):

1. Go to the **Web** tab.
2. Locate the **Static files** section.
3. Add a new entry:
   * **URL**: `/static/`
   * **Directory**: `/home/YOUR_USERNAME/iskolearn_webapp/static`

---

## Step 7: Reload and Visit Your Site!

1. Go to the top of the **Web** tab.
2. Click the big green **Reload <your-username>.pythonanywhere.com** button.
3. Open a new browser tab and navigate to `http://YOUR_USERNAME.pythonanywhere.com`.
4. Your application should now be live! The SQLite database `plrs.db` will be initialized automatically on first run.
