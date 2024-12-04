export function chunkText(text: string, chunkSize: number = 500, overlap: number = 50): string[] {
  if (!text.trim()) return [];
  
  const chunks: string[] = [];
  let start = 0;
  const textContent = text.trim();
  
  while (start < textContent.length) {
    let end = start + chunkSize;
    
    if (end > textContent.length) {
      end = textContent.length;
    } else {
      // Try to find the last period or newline before the end
      const lastPeriod = textContent.lastIndexOf('.', end);
      const lastNewline = textContent.lastIndexOf('\n', end);
      const breakPoint = Math.max(lastPeriod, lastNewline);
      
      if (breakPoint > start) {
        end = breakPoint + 1;
      }
    }
    
    const chunk = textContent.slice(start, end).trim();
    if (chunk) {
      chunks.push(chunk);
    }
    
    start += chunkSize - overlap;
  }
  
  return chunks;
}

export function preprocessText(text: string): string {
  // Basic text preprocessing
  return text
    .replace(/\s+/g, ' ')
    .trim();
}