/**
 * ExportService - Pure JS CSV export utility
 * @module services/ExportService
 */

export class ExportService {
    /**
     * Generate CSV string from rows.
     * @param {string[]} headers - Column headers
     * @param {Array<Array<string|number>>} rows - Data rows
     * @returns {string} CSV content
     */
    static toCSV(headers, rows) {
        const escape = (val) => {
            const str = String(val ?? '');
            return str.includes(',') || str.includes('"') || str.includes('\n')
                ? `"${str.replace(/"/g, '""')}"` : str;
        };
        const lines = [headers.map(escape).join(',')];
        for (const row of rows) {
            lines.push(row.map(escape).join(','));
        }
        return lines.join('\n');
    }

    /**
     * Trigger browser download of CSV.
     * @param {string} csv - CSV string
     * @param {string} filename - Download filename
     */
    static download(csv, filename) {
        const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Build date string for filenames.
     * @returns {string} YYYY-MM-DD
     */
    static dateStamp() {
        return new Date().toISOString().slice(0, 10);
    }
}
