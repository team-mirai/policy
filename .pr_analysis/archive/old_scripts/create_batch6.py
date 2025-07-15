#!/usr/bin/env python3
import yaml
from datetime import datetime

# Load the merged data
with open('readme-pr-merged.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

# Get classified PRs from all previous batches
batch1_prs = [6215, 6213, 6210, 6207, 6206, 6201, 6200, 6195, 6194, 6192, 
              6188, 6186, 6184, 6183, 6180, 6179, 6176, 6173, 6163, 6160]
batch2_prs = [6158, 6157, 6151, 6149, 6147, 6145, 6143, 6141, 6137, 6134,
              6133, 6132, 6130, 6129, 6123, 6121, 6119, 6118, 6115, 6112,
              6109, 6106, 6102, 6099, 6097, 6094, 6090, 6089, 6087, 6084,
              6083, 6082, 6081, 6079, 6078, 6077, 6075, 6074, 6072, 6070,
              6069, 6068, 6065, 6059, 6056, 6048, 6047, 6044, 6043, 6042]
batch3_prs = [6038, 6037, 6030, 6029, 6024, 6023, 6021, 6018, 6016, 6015,
              6011, 6010, 6009, 6004, 6002, 5998, 5997, 5996, 5995, 5990,
              5989, 5988, 5984, 5977, 5976, 5972, 5970, 5969, 5967, 5966,
              5965, 5964, 5962, 5960, 5959, 5957, 5953, 5952, 5950, 5949,
              5947, 5944, 5930, 5928, 5924, 5920, 5919, 5917, 5908, 5906]
batch4_prs = [5822, 5817, 5816, 5813, 5799, 5798, 5797, 5796, 5793, 5785,
              5774, 5772, 5771, 5770, 5767, 5766, 5763, 5762, 5758, 5756,
              5753, 5748, 5746, 5745, 5742, 5732, 5730, 5728, 5726, 5722,
              5719, 5718, 5715, 5713, 5707, 5704, 5700, 5694, 5690, 5688,
              5687, 5686, 5685, 5676, 5672, 5659, 5649, 5648, 5647, 5645]
batch5_prs = [6154, 6152, 6150, 6148, 6146, 6142, 6139, 6135, 6128, 6124,
              6114, 6110, 6108, 6107, 6105, 6095, 6092, 6091, 6071, 6063,
              6054, 6053, 6046, 6045, 6040, 6033, 6008, 6006, 6001, 5999,
              5994, 5992, 5983, 5982, 5981, 5980, 5971, 5963, 5958, 5956,
              5943, 5940, 5939, 5938, 5933, 5932, 5910, 5903, 5896, 5893]

classified_prs = set(batch1_prs + batch2_prs + batch3_prs + batch4_prs + batch5_prs)

# Get next 50 unclassified PRs
unclassified_prs = []
for pr in data['pull_requests']:
    if pr['number'] not in classified_prs:
        unclassified_prs.append(pr)
    if len(unclassified_prs) >= 50:
        break

# Create batch 6
batch6_data = {
    'batch_metadata': {
        '作成日時': datetime.now().strftime('%Y年%m月%d日 %H:%M'),
        'バッチサイズ': len(unclassified_prs),
        '累計処理数': len(classified_prs) + len(unclassified_prs),
        '総未処理数': 513 - len(classified_prs) - len(unclassified_prs)
    },
    'pull_requests': unclassified_prs
}

# Save batch 6
filename = f"batch6_{datetime.now().strftime('%Y%m%d_%H%M')}.yaml"
with open(filename, 'w', encoding='utf-8') as f:
    yaml.dump(batch6_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

print(f"バッチ6を作成しました: {filename}")
print(f"  PR数: {len(unclassified_prs)}件")
print(f"  累計処理済み: {len(classified_prs)}件")
print(f"  今回処理: {len(unclassified_prs)}件")
print(f"  残り: {513 - len(classified_prs) - len(unclassified_prs)}件")
print("\nバッチ6のPR番号:")
for pr in unclassified_prs[:10]:
    print(f"  - {pr['number']}: {pr['title']}")