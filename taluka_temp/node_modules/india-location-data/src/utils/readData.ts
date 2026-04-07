import * as fs from "fs";
import * as path from "path";

// Read and parse data
export const readData = (filePath: string): any[] => {
  try {
    const data = fs.readFileSync(path.resolve(__dirname, filePath), "utf-8");
    return JSON.parse(data);
  } catch (error) {
    console.error(`Error reading or parsing data from ${filePath}:`, error);
    throw new Error("Error reading data");
  }
};
