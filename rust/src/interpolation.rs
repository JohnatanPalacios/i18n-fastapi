use std::collections::HashMap;

/// Replaces `{key}` placeholders in `template` with values from `params`.
/// Unmatched placeholders are left as-is.
pub fn interpolate(template: &str, params: &HashMap<String, String>) -> String {
    if params.is_empty() || !template.contains('{') {
        return template.to_string();
    }

    let mut result = String::with_capacity(template.len());
    let mut chars = template.chars().peekable();

    while let Some(ch) = chars.next() {
        if ch == '{' {
            let mut key = String::new();
            let mut found_close = false;

            for inner in chars.by_ref() {
                if inner == '}' {
                    found_close = true;
                    break;
                }
                key.push(inner);
            }

            if found_close {
                if let Some(val) = params.get(&key) {
                    result.push_str(val);
                } else {
                    result.push('{');
                    result.push_str(&key);
                    result.push('}');
                }
            } else {
                result.push('{');
                result.push_str(&key);
            }
        } else {
            result.push(ch);
        }
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_interpolation() {
        let mut params = HashMap::new();
        params.insert("id".to_string(), "abc123".to_string());
        assert_eq!(
            interpolate("Document not found: {id}", &params),
            "Document not found: abc123"
        );
    }

    #[test]
    fn test_multiple_params() {
        let mut params = HashMap::new();
        params.insert("name".to_string(), "John".to_string());
        params.insert("count".to_string(), "5".to_string());
        assert_eq!(
            interpolate("{name} has {count} items", &params),
            "John has 5 items"
        );
    }

    #[test]
    fn test_missing_param_kept() {
        let params = HashMap::new();
        assert_eq!(
            interpolate("Hello {name}", &params),
            "Hello {name}"
        );
    }

    #[test]
    fn test_no_placeholders() {
        let params = HashMap::new();
        assert_eq!(interpolate("Hello world", &params), "Hello world");
    }

    #[test]
    fn test_empty_params_shortcircuit() {
        let params = HashMap::new();
        assert_eq!(interpolate("test {x}", &params), "test {x}");
    }
}
