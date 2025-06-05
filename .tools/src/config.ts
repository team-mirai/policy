interface FileLabelMapping {
  pattern: string;
  label: string;
}

export const fileLabelMappings: FileLabelMapping[] = [
  { pattern: "README.md", label: "README" },
  { pattern: "11_ステップ１教育.md", label: "教育" },
  { pattern: "12_ステップ１子育て.md", label: "子育て" },
  { pattern: "13_ステップ１行政改革.md", label: "行政改革" },
  { pattern: "14_ステップ１産業.md", label: "産業政策" },
  { pattern: "15_ステップ１科学技術.md", label: "科学技術" },
  { pattern: "16_ステップ１デジタル民主主義.md", label: "デジタル民主主義" },
  { pattern: "17_ステップ１医療.md", label: "医療" },


  // { pattern: "20_ステップ２「変化に対応できるしなやかな仕組みづくり」.md", label: "変化対応" },
  { pattern: "21_ステップ２教育.md", label: "教育" },
  { pattern: "22_ステップ２行政改革.md", label: "行政改革" },
  { pattern: "23_ステップ２経済財政.md", label: "経済財政" },
  { pattern: "24_ステップ２医療.md", label: "医療" },

  // { pattern: "30_ステップ３「長期の成長に大胆に投資する」.md", label: "長期成長" },
  { pattern: "31_ステップ３子育て.md", label: "子育て" },
  { pattern: "32_ステップ３教育.md", label: "教育" },
  { pattern: "33_ステップ３科学技術.md", label: "科学技術" },
  { pattern: "34_ステップ３産業.md", label: "産業政策" },
  { pattern: "35_ステップ３エネルギー.md", label: "エネルギー" },
  { pattern: "36_ステップ３経済財政.md", label: "経済財政" },

  { pattern: "01_チームみらいのビジョン.md", label: "ビジョン" },
  // { pattern: "02_政策インデックス.md", label: "インデックス" },
  // { pattern: "40_国政政党成立後100日プラン.md", label: "100日プラン" },
  { pattern: "50_国政のその他重要分野.md", label: "その他政策" }
];
