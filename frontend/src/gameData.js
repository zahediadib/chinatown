const TILE_SIZE = 10;
const GAP_X = 40;
const GAP_Y = 33;

const blocks = [
  { startX: 95, startY: 114, rows: 1, cols: 2 },
  { startX: 95, startY: 157, rows: 1, cols: 3 },
  { startX: 43, startY: 199, rows: 1, cols: 4 },
  { startX: 43, startY: 242, rows: 2, cols: 3 },
  { startX: 270, startY: 112, rows: 2, cols: 3 },
  { startX: 269, startY: 196, rows: 3, cols: 2 },
  { startX: 446, startY: 112, rows: 3, cols: 3 },
  { startX: 495, startY: 240, rows: 2, cols: 3 },
  { startX: 672, startY: 114, rows: 3, cols: 4 },
  { startX: 772, startY: 242, rows: 2, cols: 2 },
  { startX: 302, startY: 363, rows: 2, cols: 2 },
  { startX: 302, startY: 448, rows: 2, cols: 3 },
  { startX: 353, startY: 534, rows: 1, cols: 2 },
  { startX: 557, startY: 362, rows: 3, cols: 4 },
  { startX: 557, startY: 490, rows: 1, cols: 3 },
];

let id = 1;
export const BOARD_TILES = [];
blocks.forEach((block) => {
  for (let r = 0; r < block.rows; r++) {
    for (let c = 0; c < block.cols; c++) {
      BOARD_TILES.push({
        id,
        x: block.startX + c * (TILE_SIZE + GAP_X),
        y: block.startY + r * (TILE_SIZE + GAP_Y),
      });
      id++;
    }
  }
});

export const BOARD_WIDTH = 920;
export const BOARD_HEIGHT = 620;

export const SHOP_TYPES = {
  PHOTO: { maxSize: 3, label: 'Photo Studio' },
  SEAFOOD: { maxSize: 3, label: 'Seafood' },
  TEAHOUSE: { maxSize: 3, label: 'Tea House' },
  JEWELLERY: { maxSize: 4, label: 'Jewellery' },
  FLORIST: { maxSize: 4, label: 'Florist' },
  TROPICALFISH: { maxSize: 4, label: 'Tropical Fish' },
  LAUNDRY: { maxSize: 5, label: 'Laundry' },
  DIMSUM: { maxSize: 5, label: 'Dim Sum' },
  TAKEOUT: { maxSize: 5, label: 'Takeout' },
  RESTAURANT: { maxSize: 6, label: 'Restaurant' },
  ANTIQUES: { maxSize: 6, label: 'Antiques' },
  FACTORY: { maxSize: 6, label: 'Factory' },
};

export const ADJACENCY = {
  1:[2,3],2:[1,4],3:[1,4,7],4:[2,3,5,8],5:[4,9],
  6:[7,10],7:[3,6,8,11],8:[4,7,9,12],9:[5,8],
  10:[6,11,13],11:[7,10,12,14],12:[8,11,15],
  13:[10,14],14:[11,13,15],15:[12,14],
  16:[17,19],17:[16,18,20],18:[17,21],
  19:[16,20,22],20:[17,19,21,23],21:[18,20],
  22:[19,23,24],23:[20,22,25],24:[22,25,26],25:[23,24,27],26:[24,27],27:[25,26],
  28:[29,31],29:[28,30,32],30:[29,33],
  31:[28,32,34],32:[29,31,33,35],33:[30,32,36],
  34:[31,35],35:[32,34,36,37],36:[33,35,38],
  37:[35,38,40],38:[36,37,39,41],39:[38,42],40:[37,41],41:[38,40,42],42:[39,41],
  43:[44,47],44:[43,45,48],45:[44,46,49],46:[45,50],
  47:[43,48,51],48:[44,47,49,52],49:[45,48,50,53],50:[46,49,54],
  51:[47,52],52:[48,51,53],53:[49,52,54,55],54:[50,53,56],
  55:[53,56,57],56:[54,55,58],57:[55,58],58:[56,57],
  59:[60,61],60:[59,62],61:[59,62,63],62:[60,61,64],
  63:[61,64,66],64:[62,63,65,67],65:[64,68],
  66:[63,67],67:[64,66,68,69],68:[65,67,70],69:[67,70],70:[68,69],
  71:[72,75],72:[71,73,76],73:[72,74,77],74:[73,78],
  75:[71,76,79],76:[72,75,77,80],77:[73,76,78,81],78:[74,77,82],
  79:[75,80,83],80:[76,79,81,84],81:[77,80,82,85],82:[78,81],
  83:[79,84],84:[80,83,85],85:[81,84],
};
