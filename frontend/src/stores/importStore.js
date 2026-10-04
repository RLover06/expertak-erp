import { writable } from 'svelte/store';

export const importStore = writable(null);
export const isLoading = writable(false);
export const error = writable(null);
export const excelPreview = writable(null);
