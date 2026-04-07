import { initialize } from "./initServices";

export const wrapService = (service: any) => {
  return new Proxy(service, {
    get(target, propKey) {
      if (typeof target[propKey] === "function") {
        return async function (...args: any[]) {
          await initialize();
          return target[propKey](...args);
        };
      }
      return target[propKey];
    },
  });
};
