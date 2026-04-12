import { clsx } from "clsx";
import { twMerge } from "tailwind-merge"

export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

const TILE_TYPE_LABELS = {
  PHOTO: 'Photo Studio',
  SEAFOOD: 'Seafood',
  TEAHOUSE: 'Tea House',
  JEWELLERY: 'Jewellery',
  FLORIST: 'Florist',
  TROPICALFISH: 'Tropical Fish',
  LAUNDRY: 'Laundry',
  DIMSUM: 'Dim Sum',
  TAKEOUT: 'Takeout',
  RESTAURANT: 'Restaurant',
  ANTIQUES: 'Antiques',
  FACTORY: 'Factory',
  ANTI: 'Antiques',
  SEAF: 'Seafood',
};

export function formatTileType(type) {
  if (!type) return '';
  const normalized = String(type).trim().toUpperCase();
  return TILE_TYPE_LABELS[normalized] || String(type);
}

export function formatUsername(username) {
  if (!username) return '';
  const value = String(username);
  return value.charAt(0).toUpperCase() + value.slice(1);
}
