use pyo3::prelude::*;

mod engine;
mod interpolation;
mod loader;
mod pluralization;

#[pymodule]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<engine::TranslationEngine>()?;
    Ok(())
}
