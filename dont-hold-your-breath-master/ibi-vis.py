import pandas as pd
import plotly.express as px
import glob

# --- ファイルを取得 ---
filepaths = sorted(glob.glob("data/test_data_ibi.csv"))

df_list = []
time_offset = 0  # 時間補正のオフセット（初期は0）

for path in filepaths:
    print(f"Processing file: {path}")
    df = pd.read_csv(path, header=None)
    df.columns = ['times', 'values']
    
    # 時間補正を適用
    df['times'] = df['times'] + time_offset
    
    # 次ファイル用に time_offset を更新
    time_offset = df['times'].iloc[-1]  # 最後の時間を次の開始オフセットに
    
    df_list.append(df)

# --- データ結合 ---
combined_df = pd.concat(df_list, ignore_index=True)

# HR = 60000 / IBI(ms)
combined_df['heart_rate'] = 60000 / combined_df['values']

# --- グラフ表示 ---
# --- 保存オプション ---
# fig.write_image("ibi_plot.png")
# fig.write_html("ibi_plot.html")
# --- 可視化（IBI）---
fig_ibi = px.line(
    combined_df,
    x='times',
    y='values',
    labels={'times': 'Time (s)', 'values': 'IBI (ms)'},
    title="Inter-Beat Interval (IBI) over Time"
)
fig_ibi.show()

# --- ✅ 可視化（心拍数）---
fig_hr = px.line(
    combined_df,
    x='times',
    y='heart_rate',
    labels={'times': 'Time (s)', 'heart_rate': 'Heart Rate (bpm)'},
    title="Heart Rate over Time"
)
fig_hr.show()

# --- （任意）画像として保存も可能 ---
# fig_ibi.write_image("ibi_plot.png")
# fig_hr.write_image("heart_rate_plot.png")