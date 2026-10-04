<?php
/**
 * Simple Autoloader
 * 
 * PSR-4 compatible autoloader for the Expertak namespace
 * 
 * @package Expertak\Includes
 */

spl_autoload_register(function ($className) {
    // Remove namespace prefix
    $prefix = 'Expertak\\';
    $baseDir = __DIR__ . '/../';

    // Check if class uses the namespace prefix
    $len = strlen($prefix);
    if (strncmp($prefix, $className, $len) !== 0) {
        return;
    }

    // Get relative class name
    $relativeClass = substr($className, $len);

    // Map namespace to directory structure
    // Expertak\Config\* -> config/*
    // Expertak\Includes\* -> includes/*
    if (strpos($relativeClass, 'Config\\') === 0) {
        $file = $baseDir . 'config/' . substr($relativeClass, 7) . '.php';
    } elseif (strpos($relativeClass, 'Includes\\') === 0) {
        $file = $baseDir . 'includes/' . substr($relativeClass, 9) . '.php';
    } else {
        // Fallback: replace namespace separators with directory separators
        $file = $baseDir . str_replace('\\', '/', $relativeClass) . '.php';
    }

    // If file exists, require it
    if (file_exists($file)) {
        require $file;
    }
});
