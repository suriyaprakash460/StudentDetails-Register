/**
 * Validates if the input is a non-empty string.
 * @param input - The input value to be checked.
 * @param paramName - The name of the parameter being checked, for better error messages.
 * @returns True if the input is valid, otherwise throws an error.
 */

export const validateString = (input: any, paramName: string): boolean => {
  if (typeof input !== "string" || input.trim() === "") {
    throw new Error(`Invalid ${paramName} provided`);
  }
  return true;
};

/**
 * Throws an error if the item is not found.
 * @param item - The item to check.
 * @param itemName - The name of the item being checked, for better error messages.
 */
export const logItemNotFound = (item: any, itemName: string): void => {
  if (!item) {
    throw new Error(`${itemName} not found`);
  }
};
