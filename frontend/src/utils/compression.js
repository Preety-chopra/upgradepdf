export function getCompressionResult(job) {
  if (
    job?.operation !== "compress" ||
    job.status !== "completed" ||
    !Number.isFinite(job.input_size_bytes) ||
    !Number.isFinite(job.output_size_bytes) ||
    job.input_size_bytes <= 0 ||
    job.output_size_bytes < 0
  ) {
    return null;
  }

  const reduced = job.output_size_bytes < job.input_size_bytes;
  const percent = ((job.input_size_bytes - job.output_size_bytes) / job.input_size_bytes) * 100;
  const rounded = Number(percent.toFixed(1));

  return {
    reduced,
    title: reduced ? "Your compressed PDF is ready" : "PDF could not be reduced",
    message: reduced
      ? "Your PDF file size has been reduced successfully."
      : "This PDF could not be made smaller at the selected level. Try a stronger compression level or keep your original file.",
    savings: reduced
      ? `${rounded === 0 ? "<0.1" : rounded}% space saved`
      : "No size reduction"
  };
}
