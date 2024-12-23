use anyhow::Result;
use clap::Parser;
use image::{GenericImage, GenericImageView};
use std::fs;
use std::io::Write;
use std::path::Path;

fn get_img(path: &str, alpha_center: bool) -> Result<image::DynamicImage> {
    let img = image::open(path)?;

    if !alpha_center {
        Ok(img)
    } else {
        let (x, y) = img.dimensions();
        let rgb_img = img.to_rgba8();

        let mut x_left = x;
        let mut x_right = 0;
        for x0 in 0..x {
            let mut y_is_transparent = true;
            for y0 in 0..y {
                let pix = rgb_img.get_pixel(x0, y0);
                if pix[3] != 0 {
                    y_is_transparent = false;
                    break;
                }
            }
            if !y_is_transparent {
                if x0 < x_left {
                    x_left = if x0 > 0 { x0 - 1 } else { 0 };
                }
                if x0 > x_right {
                    x_right = if x0 < x { x0 + 1 } else { x };
                }
            }
        }

        let mut y_top = 0;
        let mut y_bottom = y;
        for y0 in 0..y {
            let mut x_is_transparent = true;
            for x0 in 0..x {
                let pix = rgb_img.get_pixel(x0, y0);
                if pix[3] != 0 {
                    x_is_transparent = false;
                    break;
                }
            }
            if !x_is_transparent {
                if y0 < y_bottom {
                    y_bottom = if y0 > 0 { y0 - 1 } else { 0 };
                }
                if y0 > y_top {
                    y_top = if y0 < y { y0 + 1 } else { y };
                }
            }
        }

        let true_w = x_right - x_left;
        let true_h = y_top - y_bottom;

        let mut new_img = image::DynamicImage::new_rgba8(true_w, true_h);
        new_img.copy_from(&rgb_img, x_left, y_bottom)?;
        let name = Path::new(path).file_stem().unwrap().to_str().unwrap();
        println!(
            "{} x_left {} y_bottom {} x_right {} y_top {}",
            name, x_left, y_bottom, x_right, y_top
        );

        Ok(new_img)
    }
}

/// Create fnt file from images in folder 创建fnt文件
#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// Using files in folder 使用文件夹内的文件
    #[arg(short, long)]
    folder_path: String,

    /// Only use files with specified extension 文件夹内仅搜索这类扩展名
    #[arg(short, long, default_value = ".png")]
    extension: String,

    /// 0 [default]: 使用图片大小 1: 使用alpha中心大小
    #[arg(short, long, default_value_t = 0)]
    alpha_center: u8,

    /// Set the fnt png image's max width 创建的fnt图片文件最大宽度，默认 1024
    #[arg(short, long, default_value_t = 1024)]
    max_des_width: u32,

    /// Set the fnt png image's char width offset 创建的fnt图片单字间距，默认 0
    #[arg(short, long, default_value_t = 0_u32)]
    char_width_offset: u32,
}

fn make_fnt() -> Result<()> {
    let args: Args = Args::parse();
    let folder_path = Path::new(&args.folder_path);
    let alpha_center = args.alpha_center == 1;
    let extension = args.extension;
    let max_des_width = args.max_des_width;
    let char_width_offset = args.char_width_offset;

    let mut img_list: std::collections::BTreeMap<String, image::DynamicImage> =
        std::collections::BTreeMap::new();

    let mut cell_max_width = 0;
    let mut cell_max_height = 0;

    if let Ok(entries) = fs::read_dir(folder_path) {
        for entry in entries.flatten() {
            let file_path = entry.path();
            if file_path.is_file() {
                if let Some(file_name) = file_path.file_name() {
                    let file_name = file_name.to_str().unwrap();
                    if file_name.to_lowercase().ends_with(&extension) {
                        let name = file_path.file_stem().unwrap().to_str().unwrap().to_string();
                        let img = get_img(file_path.to_str().unwrap(), alpha_center)?;

                        img_list.insert(name, img.clone());
                        if cell_max_width < img.width() {
                            cell_max_width = img.width();
                        }
                        if cell_max_height < img.height() {
                            cell_max_height = img.height();
                        }
                    }
                }
            }
        }
    }

    if img_list.is_empty() {
        anyhow::bail!("No image found in folder");
    }

    let line_cnt = (max_des_width - (max_des_width % cell_max_width)) / cell_max_width;
    let cell_cnt = img_list.len() as u32;

    let (page_width, page_height) = if cell_cnt > line_cnt {
        if cell_cnt % line_cnt > 0 {
            let cnt = (cell_cnt - (cell_cnt % line_cnt)) / line_cnt + 1;
            (max_des_width, cell_max_height * cnt)
        } else {
            let cnt = (cell_cnt - (cell_cnt % line_cnt)) / line_cnt;
            (max_des_width, cell_max_height * cnt)
        }
    } else {
        (cell_max_width * cell_cnt, cell_max_height)
    };

    let mut str_fnt = format!(
        "info face=\"Arial\" size={} bold=0 italic=0 charset=\"\" unicode=0 stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=2,2\n",
        cell_max_height
    );
    str_fnt += &format!(
        "common lineHeight={} base=20 scaleW={} scaleH={} pages=1 packed=0\n",
        cell_max_height, page_width, page_height
    );
    let fn_name = folder_path.file_name().unwrap().to_str().unwrap();
    let fn_image_name = format!("{}.png", fn_name);
    str_fnt += &format!("page id=0 file=\"{}\"\n", fn_image_name);
    str_fnt += &format!("chars count={}\n", img_list.len() + 1);

    let mut key_list: Vec<&String> = img_list.keys().collect();
    key_list.sort();

    let mut des_img = image::DynamicImage::new_rgba8(page_width, page_height);

    str_fnt += &format!(
        "char id=32 x=0 y=0 width=0 height=0 xoffset=0 yoffset=0 xadvance={} page=0 chnl=0 letter=\"space\"\n",
        cell_max_width + char_width_offset
    );

    let mut left = 0;
    let mut top = 0;
    let mut line_no = 0;
    for key in key_list {
        let img = img_list.get(key).unwrap();
        let (w, h) = img.dimensions();
        let char_code = key.chars().next().unwrap() as u32;

        let x = left + ((cell_max_width - w) / 2);
        let y = top + ((cell_max_height - h) / 2);

        des_img.copy_from(img, x, y)?;

        str_fnt += &format!(
            "char id={} x={} y={} width={} height={} xoffset=0 yoffset=0 xadvance={} page=0 chnl=0 letter=\"{}\"\n",
            char_code, x, top, w, cell_max_height, w + char_width_offset, key
        );

        line_no += 1;
        if line_no < line_cnt {
            left += cell_max_width;
        } else {
            line_no = 0;
            left = 0;
            top += cell_max_height;
        }
    }

    des_img.save(folder_path.parent().unwrap().join(fn_image_name))?;

    let mut f = fs::File::create(
        folder_path
            .parent()
            .unwrap()
            .join(format!("{}.fnt", fn_name)),
    )?;
    f.write_all(str_fnt.as_bytes())?;

    Ok(())
}

fn main() {
    make_fnt().unwrap();
}
