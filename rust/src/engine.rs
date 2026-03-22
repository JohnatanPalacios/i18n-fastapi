use std::collections::HashMap;
use std::path::PathBuf;

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

use crate::interpolation::interpolate;
use crate::loader;
use crate::pluralization::PluralForms;

/// A translation value: either a simple string or ICU plural forms.
#[derive(Debug, Clone)]
pub enum TranslationValue {
    Simple(String),
    Plural(PluralForms),
}

/// The core translation engine. Stores all translations in flat HashMaps
/// keyed by dot-separated paths (e.g. "documents.errors.notFound").
#[pyclass]
pub struct TranslationEngine {
    translations: HashMap<String, HashMap<String, TranslationValue>>,
    default_locale: String,
    raise_on_duplicate: bool,
    locale_dir_name: String,
    loaded_dirs: Vec<PathBuf>,
    missing_keys: Vec<(String, String)>,
}

#[pymethods]
impl TranslationEngine {
    #[new]
    #[pyo3(signature = (default_locale, raise_on_duplicate=true, locale_dir_name="locales".to_string()))]
    fn new(
        default_locale: String,
        raise_on_duplicate: bool,
        locale_dir_name: String,
    ) -> Self {
        TranslationEngine {
            translations: HashMap::new(),
            default_locale,
            raise_on_duplicate,
            locale_dir_name,
            loaded_dirs: Vec::new(),
            missing_keys: Vec::new(),
        }
    }

    /// Auto-discover locale directories starting from `root_path`.
    fn auto_discover(&mut self, root_path: String) -> PyResult<()> {
        let root = PathBuf::from(&root_path);
        let project_root = loader::find_project_root(&root);
        let dirs = loader::scan_locale_dirs(&project_root, &self.locale_dir_name);

        for dir in dirs {
            self.load_dir_internal(&dir)?;
        }

        Ok(())
    }

    /// Load a specific locale directory.
    fn load_locale_dir(&mut self, path: String) -> PyResult<()> {
        let dir = PathBuf::from(path);
        self.load_dir_internal(&dir)
    }

    /// Translate a key with optional parameters.
    /// If a `count` param is present and the value is a plural form,
    /// the appropriate plural category is selected.
    #[pyo3(signature = (key, locale, params=HashMap::new()))]
    fn translate(
        &mut self,
        key: &str,
        locale: &str,
        params: HashMap<String, String>,
    ) -> String {
        let val = self.lookup(key, locale);

        if val.is_none() {
            self.missing_keys.push((key.to_string(), locale.to_string()));
            return key.to_string();
        }

        let val = val.unwrap();

        match val {
            TranslationValue::Simple(s) => interpolate(s, &params),
            TranslationValue::Plural(forms) => {
                let count = params
                    .get("count")
                    .and_then(|c| c.parse::<i64>().ok())
                    .unwrap_or(0);

                let template = forms.select(count);
                interpolate(template, &params)
            }
        }
    }

    /// Return all loaded locale codes.
    fn available_locales(&self) -> Vec<String> {
        let mut locales: Vec<String> = self.translations.keys().cloned().collect();
        locales.sort();
        locales
    }

    /// Reload all previously loaded directories.
    fn reload(&mut self) -> PyResult<()> {
        let dirs = self.loaded_dirs.clone();
        self.translations.clear();
        self.missing_keys.clear();

        for dir in &dirs {
            self.load_dir_internal(dir)?;
        }

        Ok(())
    }

    /// Return accumulated missing key lookups as (key, locale) pairs.
    fn get_missing_keys(&self) -> Vec<(String, String)> {
        self.missing_keys.clone()
    }

    /// Clear the missing keys log.
    fn clear_missing_keys(&mut self) {
        self.missing_keys.clear();
    }

    /// Check if a specific translation key exists for a locale.
    fn has_key(&self, key: &str, locale: &str) -> bool {
        self.lookup(key, locale).is_some()
    }

    /// Return loaded directory paths.
    fn loaded_directories(&self) -> Vec<String> {
        self.loaded_dirs
            .iter()
            .filter_map(|p| p.to_str().map(|s| s.to_string()))
            .collect()
    }
}

impl TranslationEngine {
    fn load_dir_internal(&mut self, dir: &PathBuf) -> PyResult<()> {
        let loaded = loader::load_locale_dir(dir, self.raise_on_duplicate)
            .map_err(|e| PyValueError::new_err(e))?;

        for (lang, entries) in loaded {
            let lang_map = self.translations.entry(lang.clone()).or_default();

            for (key, value) in entries {
                if self.raise_on_duplicate && lang_map.contains_key(&key) {
                    return Err(PyValueError::new_err(format!(
                        "DuplicateKeyError: Key \"{}\" for locale \"{}\" already loaded \
                         from a previously loaded directory, conflicting directory: \"{}\"",
                        key,
                        lang,
                        dir.display()
                    )));
                }
                lang_map.insert(key, value);
            }
        }

        if !self.loaded_dirs.contains(dir) {
            self.loaded_dirs.push(dir.clone());
        }

        Ok(())
    }

    fn lookup(&self, key: &str, locale: &str) -> Option<&TranslationValue> {
        if let Some(lang_map) = self.translations.get(locale) {
            if let Some(val) = lang_map.get(key) {
                return Some(val);
            }
        }

        if locale != self.default_locale {
            if let Some(default_map) = self.translations.get(&self.default_locale) {
                if let Some(val) = default_map.get(key) {
                    return Some(val);
                }
            }
        }

        None
    }
}
