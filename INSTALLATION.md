# Installation Guide

## Quick Start

Follow these steps to set up the Excel Import System on your server.

## Prerequisites

- PHP 8.0 or higher
- MariaDB 10.4+ or MySQL 5.7+
- Web server (Apache or Nginx)
- Composer (optional, for dependency management)

## Step 1: Upload Files

Upload all project files to your web server:

```
/public_html/expertak/
```

Or for cPanel:
```
/home/username/public_html/expertak/
```

## Step 2: Install Dependencies

### Option A: Using Composer (Recommended)

```bash
cd /path/to/expertak
composer install
```

### Option B: Manual Installation

1. Download PhpSpreadsheet from: https://github.com/PHPOffice/PhpSpreadsheet/releases
2. Extract to: `vendor/phpoffice/phpspreadsheet/`
3. Ensure directory structure: `vendor/phpoffice/phpspreadsheet/src/PhpSpreadsheet/`

## Step 3: Database Setup

### Create Database

```sql
CREATE DATABASE expertak CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Create Table

```bash
mysql -u username -p expertak < sql/create_import_table.sql
```

Or via phpMyAdmin:
1. Select `expertak` database
2. Go to "Import" tab
3. Choose `sql/create_import_table.sql`
4. Click "Go"

## Step 4: Configure Database Connection

Edit `config/database.php`:

```php
private const DB_HOST = 'localhost';      // Your database host
private const DB_NAME = 'expertak';       // Your database name
private const DB_USER = 'your_username';  // Your database username
private const DB_PASS = 'your_password';  // Your database password
```

**For cPanel:**
- Host: Usually `localhost`
- Database: Created in cPanel
- Username: cPanel database user
- Password: cPanel database password

## Step 5: Set Permissions

### Linux/Unix

```bash
chmod 755 uploads/
chown www-data:www-data uploads/  # Adjust user/group as needed
```

### cPanel

1. Go to File Manager
2. Navigate to `uploads/` directory
3. Right-click → Change Permissions
4. Set to `755` or `777` (if 755 doesn't work)

## Step 6: Configure PHP Settings

### Check PHP Version

```bash
php -v
```

Should be PHP 8.0 or higher.

### Check Required Extensions

```bash
php -m | grep -E "pdo|pdo_mysql|mbstring|fileinfo|zip|xml"
```

All should be present.

### Adjust PHP Limits (if needed)

Edit `php.ini` or create `.user.ini` in project root:

```ini
upload_max_filesize = 50M
post_max_size = 50M
max_execution_time = 300
memory_limit = 512M
max_input_time = 300
```

**For cPanel:**
- Go to "Select PHP Version"
- Click "Options"
- Adjust values as needed

## Step 7: Web Server Configuration

### Apache

1. Ensure `.htaccess` is in project root
2. Enable `mod_rewrite`:
   ```bash
   sudo a2enmod rewrite
   sudo systemctl restart apache2
   ```
3. Point document root to project root (or `public/` directory)

### Nginx

Add to server configuration:

```nginx
location / {
    try_files $uri $uri/ /public/index.php?$query_string;
}

location ~ ^/(config|includes|sql|uploads)/ {
    deny all;
}
```

### cPanel

1. `.htaccess` should work automatically
2. If not, contact hosting support

## Step 8: Test Installation

### 1. Test Database Connection

Create `test_db.php` in project root:

```php
<?php
require_once 'includes/autoload.php';
use Expertak\Config\Database;

if (Database::testConnection()) {
    echo "Database connection: OK";
} else {
    echo "Database connection: FAILED";
}
```

Access: `http://your-domain/test_db.php`

**Delete this file after testing!**

### 2. Test File Upload

1. Open: `http://your-domain/public/index.php`
2. Upload a test Excel file
3. Check results

### 3. Check Error Logs

If errors occur, check:
- PHP error log
- Apache/Nginx error log
- cPanel error log

## Step 9: Security Hardening

### 1. Protect Sensitive Directories

Ensure `.htaccess` rules are active:
- `/config/` - Denied
- `/includes/` - Denied
- `/sql/` - Denied
- `/uploads/` - Allowed (or restrict if needed)

### 2. Remove Test Files

Delete any test files:
- `test_db.php`
- Sample/test Excel files

### 3. Set Proper File Permissions

```bash
find . -type f -exec chmod 644 {} \;
find . -type d -exec chmod 755 {} \;
chmod 755 uploads/
```

### 4. Disable Error Display (Production)

In `api/import.php`, ensure:
```php
ini_set('display_errors', 0);
```

## Troubleshooting

### "Database connection failed"

**Solutions:**
1. Check credentials in `config/database.php`
2. Verify database exists
3. Check user permissions
4. Test connection manually:
   ```bash
   mysql -u username -p -h localhost expertak
   ```

### "File upload failed"

**Solutions:**
1. Check `upload_max_filesize` in php.ini
2. Check `post_max_size` in php.ini
3. Verify `uploads/` directory permissions
4. Check disk space

### "Class not found" or "Cannot find class"

**Solutions:**
1. Verify Composer dependencies installed
2. Check autoloader path in `includes/autoload.php`
3. Verify namespace matches directory structure
4. Clear any OPcache:
   ```bash
   php -r "opcache_reset();"
   ```

### "Column count mismatch"

**Solutions:**
1. Verify Excel file has exactly 12 columns
2. Check header row matches expected structure
3. Ensure no merged cells in header row
4. Verify column names match exactly (case-insensitive)

### "Memory limit exceeded"

**Solutions:**
1. Increase `memory_limit` in php.ini
2. Reduce `BATCH_SIZE` in `config/constants.php`
3. Process smaller files
4. Increase server memory allocation

### "Execution time exceeded"

**Solutions:**
1. Increase `max_execution_time` in php.ini
2. Increase `MAX_EXECUTION_TIME` in `config/constants.php`
3. Process files in smaller batches
4. Optimize database (add indexes)

## Verification Checklist

- [ ] PHP 8.0+ installed
- [ ] Required PHP extensions enabled
- [ ] Database created
- [ ] Table created (`documentos_contables`)
- [ ] Database credentials configured
- [ ] Dependencies installed (PhpSpreadsheet)
- [ ] `uploads/` directory writable
- [ ] PHP limits configured
- [ ] Web server configured
- [ ] `.htaccess` working
- [ ] Test import successful
- [ ] Error logging working
- [ ] Security measures in place

## Next Steps

1. Review `README.md` for usage instructions
2. Read `WORKFLOW.md` for process details
3. Check `ERROR_HANDLING.md` for error management
4. Customize constants in `config/constants.php` if needed
5. Set up monitoring and backups

## Support

For issues:
1. Check error logs
2. Review documentation
3. Verify configuration
4. Test with sample file

---

**Last Updated**: January 2026
