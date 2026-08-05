import { FileCode, FileSpreadsheet, FileText, FileType2 } from "lucide-react";

export const ACCEPTED_EXTENSIONS = [".pdf", ".docx", ".csv", ".txt", ".md"];

const ICON_BY_EXTENSION = {
  pdf: FileText,
  docx: FileType2,
  csv: FileSpreadsheet,
  txt: FileText,
  md: FileCode,
};

export function getExtension(filename) {
  const match = /\.([a-z0-9]+)$/i.exec(filename);
  return match ? match[1].toLowerCase() : "";
}

export function isAcceptedFile(filename) {
  return ACCEPTED_EXTENSIONS.includes(`.${getExtension(filename)}`);
}

export function getFileIcon(filename) {
  return ICON_BY_EXTENSION[getExtension(filename)] || FileText;
}
