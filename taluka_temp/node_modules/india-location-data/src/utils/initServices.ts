import * as stateService from "../services/stateService";
import * as districtService from "../services/districtService";
import * as blockService from "../services/blockService";
import * as villageService from "../services/villageService";
import * as cityService from "../services/cityService";
import { loadData } from "./dataLoader";

// Common initialization function
export const initServices = (data: {
  States: any[];
  Districts: any[];
  Blocks: any[];
  Villages: any[];
  Cities: any[];
}) => {
  stateService.init(data.States);
  districtService.init(data.Districts);
  blockService.init(data.Districts, data.Blocks);
  villageService.init(data.Villages, data.Blocks, data.Districts); // Pass multiple data sources
  cityService.init(data.Cities);
};

let isInitialized = false;
let initializationPromise: Promise<void> | null = null;

export const initialize = async () => {
  if (!isInitialized) {
    if (!initializationPromise) {
      initializationPromise = (async () => {
        try {
          const data = await loadData();
          initServices(data);
          isInitialized = true;
        } catch (error) {
          console.error("Failed to initialize services:", error);
          throw error;
        }
      })();
    }
    await initializationPromise;
  }
};
