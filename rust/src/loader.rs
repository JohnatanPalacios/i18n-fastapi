use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};

use crate::engine::TranslationValue;
use crate::pluralization::{is_plural_object, PluralForms};

/// Recursively scan a directory tree for folders matching `dir_name`.
/// Skips hidden dirs, __pycache__, venv, node_modules, dist, target, .git.
pub fn scan_locale_dirs(root: &Path, dir_name: &str) -> Vec<PathBuf> {
    let mut results = Vec::new();
    scan_recursive(root, dir_name, &mut results);
    results
}

fn scan_recursive(dir: &Path, target_name: &str, results: &mut Vec<PathBuf>) {
    let entries = match fs::read_dir(dir) {
        Ok(e) => e,
        Err(_) => return,
    };

    for entry in entries.flatten() {
        let path = entry.path();
        if !path.is_dir() {
            continue;
        }

        let name = match path.file_name().and_then(|n| n.to_str()) {
            Some(n) => n.to_string(),
            None => continue,
        };

        if name.starts_with('.')
            || matches!(
                name.as_str(),
                "__pycache__" | "venv" | ".venv" | "env" | "node_modules" | "dist" | "target"
            )
        {
            continue;
        }

        if name == target_name {
            results.push(path);
        } else {
            scan_recursive(&path, target_name, results);
        }
    }
}

/// Find the project root by walking up from `start_path`.
pub fn find_project_root(start_path: &Path) -> PathBuf {
    let mut current = if start_path.is_file() {
        start_path
            .parent()
            .unwrap_or(start_path)
    } else {
        start_path
    };

    loop {
        if current.join(".git").exists()
            || current.join("pyproject.toml").exists()
            || current.join("setup.py").exists()
            || current.join("setup.cfg").exists()
        {
            return current.to_path_buf();
        }

        match current.parent() {
            Some(parent) => current = parent,
            None => return start_path.to_path_buf(),
        }
    }
}

/// Load all JSON files from a single locale directory.
/// Expected structure: `<locale_dir>/<lang>/<namespace>.json`
///
/// Returns loaded translations grouped by language.
/// Errors on duplicate keys when `raise_on_duplicate` is true.
pub fn load_locale_dir(
    locale_dir: &Path,
    raise_on_duplicate: bool,
) -> Result<HashMap<String, HashMap<String, TranslationValue>>, String> {
    let mut result: HashMap<String, HashMap<String, TranslationValue>> = HashMap::new();

    if !locale_dir.exists() || !locale_dir.is_dir() {
        return Ok(result);
    }

    let lang_dirs = match fs::read_dir(locale_dir) {
        Ok(entries) => entries,
        Err(e) => return Err(format!("Cannot read locale dir {}: {}", locale_dir.display(), e)),
    };

    for lang_entry in lang_dirs.flatten() {
        let lang_path = lang_entry.path();
        if !lang_path.is_dir() {
            continue;
        }

        let lang = match lang_path.file_name().and_then(|n| n.to_str()) {
            Some(l) => l.to_string(),
            None => continue,
        };

        let json_files = collect_json_files(&lang_path);

        for file_path in json_files {
            let relative = match file_path.strip_prefix(&lang_path) {
                Ok(r) => r,
                Err(_) => continue,
            };

            let no_ext = relative.with_extension("");
            let namespace_parts: Vec<&str> = no_ext
                .components()
                .filter_map(|c| c.as_os_str().to_str())
                .collect();
            let namespace_prefix = namespace_parts.join(".");

            let content = match fs::read_to_string(&file_path) {
                Ok(c) => c,
                Err(e) => {
                    return Err(format!("Cannot read {}: {}", file_path.display(), e));
                }
            };

            let json_value: serde_json::Value = match serde_json::from_str(&content) {
                Ok(v) => v,
                Err(e) => {
                    return Err(format!("Invalid JSON in {}: {}", file_path.display(), e));
                }
            };

            let lang_translations = result.entry(lang.clone()).or_default();

            flatten_json(
                &json_value,
                &namespace_prefix,
                lang_translations,
                raise_on_duplicate,
                &file_path,
                &lang,
            )?;
        }
    }

    Ok(result)
}

fn collect_json_files(dir: &Path) -> Vec<PathBuf> {
    let mut files = Vec::new();
    collect_json_recursive(dir, &mut files);
    files
}

fn collect_json_recursive(dir: &Path, files: &mut Vec<PathBuf>) {
    if let Ok(entries) = fs::read_dir(dir) {
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                collect_json_recursive(&path, files);
            } else if path.extension().and_then(|e| e.to_str()) == Some("json") {
                files.push(path);
            }
        }
    }
}

/// Flatten a nested JSON value into dot-separated keys.
fn flatten_json(
    value: &serde_json::Value,
    prefix: &str,
    target: &mut HashMap<String, TranslationValue>,
    raise_on_duplicate: bool,
    source_file: &Path,
    lang: &str,
) -> Result<(), String> {
    match value {
        serde_json::Value::Object(map) => {
            let keys: Vec<&str> = map.keys().map(|k| k.as_str()).collect();

            if is_plural_object(&keys) {
                let forms = parse_plural_forms(map)?;
                let key = prefix.to_string();

                if raise_on_duplicate && target.contains_key(&key) {
                    return Err(format!(
                        "DuplicateKeyError: Key \"{}\" for locale \"{}\" already loaded, \
                         conflicting file: \"{}\"",
                        key,
                        lang,
                        source_file.display()
                    ));
                }

                target.insert(key, TranslationValue::Plural(forms));
            } else {
                for (k, v) in map {
                    let full_key = if prefix.is_empty() {
                        k.clone()
                    } else {
                        format!("{}.{}", prefix, k)
                    };

                    flatten_json(v, &full_key, target, raise_on_duplicate, source_file, lang)?;
                }
            }
        }
        serde_json::Value::String(s) => {
            if raise_on_duplicate && target.contains_key(prefix) {
                return Err(format!(
                    "DuplicateKeyError: Key \"{}\" for locale \"{}\" already loaded, \
                     conflicting file: \"{}\"",
                    prefix,
                    lang,
                    source_file.display()
                ));
            }
            target.insert(prefix.to_string(), TranslationValue::Simple(s.clone()));
        }
        other => {
            target.insert(
                prefix.to_string(),
                TranslationValue::Simple(other.to_string()),
            );
        }
    }

    Ok(())
}

fn parse_plural_forms(
    map: &serde_json::Map<String, serde_json::Value>,
) -> Result<PluralForms, String> {
    let get_opt = |key: &str| -> Option<String> {
        map.get(key).and_then(|v| v.as_str()).map(|s| s.to_string())
    };

    let other = get_opt("other")
        .ok_or_else(|| "Plural forms must have an 'other' key".to_string())?;

    Ok(PluralForms {
        zero: get_opt("zero"),
        one: get_opt("one"),
        two: get_opt("two"),
        few: get_opt("few"),
        many: get_opt("many"),
        other,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_find_project_root() {
        let tmp = std::env::temp_dir().join("test_i18n_root");
        let _ = fs::create_dir_all(tmp.join("sub"));
        fs::write(tmp.join("pyproject.toml"), "").unwrap();

        let root = find_project_root(&tmp.join("sub"));
        assert_eq!(root, tmp);

        let _ = fs::remove_dir_all(&tmp);
    }
}
