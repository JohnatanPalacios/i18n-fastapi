use serde::Deserialize;

/// ICU plural categories.
#[derive(Debug, Clone, Deserialize)]
pub struct PluralForms {
    pub zero: Option<String>,
    pub one: Option<String>,
    pub two: Option<String>,
    pub few: Option<String>,
    pub many: Option<String>,
    pub other: String,
}

impl PluralForms {
    /// Select the appropriate plural form based on count using CLDR rules.
    /// This implements a simplified English/Spanish-compatible rule set.
    /// For full CLDR coverage, each locale would need its own rule function.
    pub fn select(&self, count: i64) -> &str {
        if count == 0 {
            if let Some(ref z) = self.zero {
                return z;
            }
        }

        if count == 1 {
            if let Some(ref o) = self.one {
                return o;
            }
        }

        if count == 2 {
            if let Some(ref t) = self.two {
                return t;
            }
        }

        // "few" is typically 3-10 in some locales (Arabic, etc.)
        if (3..=10).contains(&count) {
            if let Some(ref f) = self.few {
                return f;
            }
        }

        // "many" is typically 11-99 in some locales
        if (11..=99).contains(&count) {
            if let Some(ref m) = self.many {
                return m;
            }
        }

        &self.other
    }
}

/// Checks if a JSON object looks like a plural definition.
/// It must have an "other" key and at least one ICU category key.
pub fn is_plural_object(keys: &[&str]) -> bool {
    let icu_keys = ["zero", "one", "two", "few", "many", "other"];
    let has_other = keys.contains(&"other");
    let all_icu = keys.iter().all(|k| icu_keys.contains(k));
    has_other && all_icu && keys.len() >= 2
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_forms() -> PluralForms {
        PluralForms {
            zero: Some("No items".to_string()),
            one: Some("{count} item".to_string()),
            two: Some("{count} items".to_string()),
            few: Some("{count} items (few)".to_string()),
            many: Some("{count} items (many)".to_string()),
            other: "{count} items".to_string(),
        }
    }

    #[test]
    fn test_zero() {
        assert_eq!(make_forms().select(0), "No items");
    }

    #[test]
    fn test_one() {
        assert_eq!(make_forms().select(1), "{count} item");
    }

    #[test]
    fn test_two() {
        assert_eq!(make_forms().select(2), "{count} items");
    }

    #[test]
    fn test_few() {
        assert_eq!(make_forms().select(5), "{count} items (few)");
    }

    #[test]
    fn test_many() {
        assert_eq!(make_forms().select(50), "{count} items (many)");
    }

    #[test]
    fn test_other() {
        assert_eq!(make_forms().select(100), "{count} items");
    }

    #[test]
    fn test_is_plural_object() {
        assert!(is_plural_object(&["one", "other"]));
        assert!(is_plural_object(&["zero", "one", "two", "few", "many", "other"]));
        assert!(!is_plural_object(&["one"])); // no "other"
        assert!(!is_plural_object(&["other"])); // only 1 key
        assert!(!is_plural_object(&["other", "notFound"])); // non-ICU key
    }
}
