import os
import requests
import textgrid

def generate_100_clean_boards(audio_dir, target_dir, target_amount=100):
    
    #自动获取并清洗 TextGrid，凑齐100个后自动停止。
    ###自动跳过损坏的音频和处理失败的文件。
    
    url = "https://clarin.phonetik.uni-muenchen.de/BASWebServices/services/runMAUS"
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        
    print(f" 开始全自动生成 Praat 盲标模板 (目标: {target_amount} 个)...")
    success_count = 0
    failed_files = []

    # 排序一下，保证它是按 000, 001, 002 的顺序挨个处理
    all_files = sorted(os.listdir(audio_dir))

    for filename in all_files:
        # 如果已经凑齐 100 个，直接结束整个循环！
        if success_count >= target_amount:
            print(f"\n 太棒了！已经成功收集齐 {target_amount} 个完美的盲标模板，提前打卡下班！")
            break

        if filename.endswith(".wav"):
            base_name = os.path.splitext(filename)[0]
            wav_path = os.path.join(audio_dir, filename)
            par_path = os.path.join(audio_dir, f"{base_name}.par")
            final_target_path = os.path.join(target_dir, f"{base_name}_MAN.TextGrid")
            
            # 如果已经存在，说明之前跑成功过，直接算入 100 的名额里
            if os.path.exists(final_target_path):
                print(f" {base_name}_MAN.TextGrid 已存在，直接计入进度。")
                success_count += 1
                continue

            # 遇到坏数据 (比如没有配对的 par 文件) -> 记录并跳过
            if not os.path.exists(par_path):
                failed_files.append(f"{base_name} (找不到原始文本)")
                continue
                
            print(f" 正在向 WebMAUS 获取并清洗: {base_name} ... ({success_count}/{target_amount})")
            
            files = {'SIGNAL': open(wav_path, 'rb'), 'BPF': open(par_path, 'rb')}
            data = {'LANGUAGE': 'deu-DE', 'OUTFORMAT': 'TextGrid'} 
            
            try:
                response = requests.post(url, files=files, data=data)
                
                # 如果服务器成功处理
                if response.status_code == 200 and "<downloadLink>" in response.text:
                    link_start = response.text.find("<downloadLink>") + len("<downloadLink>")
                    link_end = response.text.find("</downloadLink>")
                    download_url = response.text[link_start:link_end]
                    
                    result_response = requests.get(download_url)
                    temp_path = os.path.join(target_dir, f"temp_{base_name}.TextGrid")
                    
                    with open(temp_path, 'wb') as f:
                        f.write(result_response.content)
                        
                    tg = textgrid.TextGrid.fromFile(temp_path)
                    new_tg = textgrid.TextGrid(name=tg.name, minTime=tg.minTime, maxTime=tg.maxTime)
                    
                    try:
                        # 尝试提取 ORT 层，如果连单词层都没有，说明文件损坏，报错跳过
                        ort_tier = tg.getFirst("ORT-MAU")
                        new_tg.append(ort_tier)
                    except ValueError:
                        failed_files.append(f"{base_name} (服务器返回的文件缺失 ORT 轨道)")
                        os.remove(temp_path) 
                        continue
                        
                    man_tier = textgrid.IntervalTier(name="MAN", minTime=tg.minTime, maxTime=tg.maxTime)
                    man_tier.add(tg.minTime, tg.maxTime, "")
                    new_tg.append(man_tier)
                    
                    new_tg.write(final_target_path)
                    os.remove(temp_path)
                    
                    print(f" 成功生成模板: {base_name}_MAN.TextGrid")
                    success_count += 1
                    
                # 如果遇到了 094 这种情况（服务器拒收）
                else:
                    failed_files.append(f"{base_name} (WebMAUS 服务器处理失败，可能是音频杂音过大)")
                    print(f" {base_name} 被服务器拒绝，已跳过。")
                    
            except Exception as e:
                failed_files.append(f"{base_name} (网络错误: {e})")
            finally:
                files['SIGNAL'].close()
                files['BPF'].close()

    print("\n" + "=" * 45)
    print(f" 最终汇报 -> 成功获得: {success_count} 个 | 剔除坏数据: {len(failed_files)} 个")
    
    if failed_files:
        print("\n 以下是没能通过清洗的“坏数据”名单（已全自动略过）：")
        for f in failed_files:
            print(f" - {f}")
    print("=" * 45)

if __name__ == '__main__':
    # 原始文件所在的目录
    source_folder = r'C:\Users\dkl31\Desktop\001 von SC2' 
    
    # 你存放纯净模板的目标目录
    target_folder = r'C:\Users\dkl31\Desktop\001 von SC2\Praat_webmaus'
    
    # 启动程序！
    generate_100_clean_boards(source_folder, target_folder)