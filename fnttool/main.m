//
//  main.m
//  fnttool
//
//  Created by HanShaokun on 23/12/2015.
//  Copyright © 2015 darklinden. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <AppKit/AppKit.h>
#import <CoreGraphics/CoreGraphics.h>

NSDictionary* infoDict()
{
    return
    @{
      @"info":
          @{@"face":@"This is the name of the true type font.",
            @"size":@"The size of the true type font.",
            @"bold":@"The font is bold.",
            @"italic":@"The font is italic.",
            @"charset":@"The name of the OEM charset used (when not unicode).",
            @"unicode":@"Set to 1 if it is the unicode charset.",
            @"stretchH":@"The font height stretch in percentage. 100% means no stretch.",
            @"smooth":@"Set to 1 if smoothing was turned on.",
            @"aa":@"The supersampling level used. 1 means no supersampling was used.",
            @"padding":@"The padding for each character (up, right, down, left).",
            @"spacing":@"The spacing for each character (horizontal, vertical).",
            @"outline":@"The outline thickness for the characters."},
      @"common":
          @{@"lineHeight":@"This is the distance in pixels between each line of text.",
            @"base":@"The number of pixels from the absolute top of the line to the base of the characters.",
            @"scaleW":@"The width of the texture, normally used to scale the x pos of the character image.",
            @"scaleH":@"The height of the texture, normally used to scale the y pos of the character image.",
            @"pages":@"The number of texture pages included in the font.",
            @"packed":@"Set to 1 if the monochrome characters have been packed into each of the texture channels. In this case alphaChnl describes what is stored in each channel.",
            @"alphaChnl":@"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.",
            @"redChnl":@"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.",
            @"greenChnl":@"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one.",
            @"blueChnl":@"Set to 0 if the channel holds the glyph data, 1 if it holds the outline, 2 if it holds the glyph and the outline, 3 if its set to zero, and 4 if its set to one."},
      @"page":
          @{@"id":@"The page id.",
            @"file":@"The texture file name."},
      @"chars":
          @{@"count":@"The number of chars does the fnt file hold."},
      @"char":
          @{@"id":@"The character id.",
              @"x":@"The left position of the character image in the texture.",
              @"y":@"The top position of the character image in the texture.",
              @"width":@"The width of the character image in the texture.",
              @"height":@"The height of the character image in the texture.",
              @"xoffset":@"How much the current position should be offset when copying the image from the texture to the screen.",
              @"yoffset":@"How much the current position should be offset when copying the image from the texture to the screen.",
              @"xadvance":@"How much the current position should be advanced after drawing the character.",
              @"page":@"The texture page where the character image is found.",
              @"chnl":@"The texture channel where the character image is found (1 = blue, 2 = green, 4 = red, 8 = alpha, 15 = all channels)."}
      };
}

NSDictionary* searchInfo(NSString* key)
{
    NSMutableDictionary* dict = [NSMutableDictionary dictionary];
    
    for (NSString* rootkey in infoDict().allKeys) {
        if ([rootkey rangeOfString:key options:NSCaseInsensitiveSearch].location != NSNotFound) {
            dict[rootkey] = infoDict()[rootkey];
        }
        else {
            NSDictionary* subdict = infoDict()[rootkey];
            NSMutableDictionary* desSubDict = [NSMutableDictionary dictionary];
            for (NSString* subkey in subdict.allKeys) {
                if ([subkey rangeOfString:key options:NSCaseInsensitiveSearch].location != NSNotFound) {
                    desSubDict[subkey] = subdict[subkey];
                }
            }
            
            if (desSubDict.count) {
                dict[rootkey] = desSubDict;
            }
        }
    }
    
    return dict;
}

BOOL CGImageWriteToFile(CGImageRef image, NSString *path) {
    CFURLRef url = (__bridge CFURLRef)[NSURL fileURLWithPath:path];
    CGImageDestinationRef destination = CGImageDestinationCreateWithURL(url, kUTTypePNG, 1, NULL);
    if (!destination) {
        NSLog(@"Failed to create CGImageDestination for %@", path);
        return NO;
    }
    
    CGImageDestinationAddImage(destination, image, nil);
    
    if (!CGImageDestinationFinalize(destination)) {
        NSLog(@"Failed to write image to %@", path);
        CFRelease(destination);
        return NO;
    }
    
    CFRelease(destination);
    return YES;
}

static NSDictionary* _params = nil;

NSDictionary* allImgs(NSString* folder, NSString* extension)
{
    NSMutableDictionary* dict = [NSMutableDictionary dictionary];
    NSArray* array = [[NSFileManager defaultManager] contentsOfDirectoryAtPath:folder error:nil];
    for (NSString *name in array) {
        if ([name.pathExtension.lowercaseString isEqualToString:extension.lowercaseString]) {
            NSString* path = [folder stringByAppendingPathComponent:name];
            
            NSString* sn = [name stringByDeletingPathExtension];
            
            NSData *imageData = [[NSData alloc] initWithContentsOfFile:path];
            CGImageSourceRef imageSource = CGImageSourceCreateWithData((__bridge CFDataRef)imageData, NULL);
            
            CGImageRef imgRef = CGImageSourceCreateImageAtIndex(imageSource, 0, NULL);
            
            dict[sn] = (__bridge id _Nullable)(imgRef);
        }
    }
    
    return dict;
}

void makeFnt(NSString* folder, NSString* extension, NSString* desName, NSString* maxWidth)
{
    NSMutableString* _strFnt = nil;

    NSString* _desName = desName;
    if (!_desName.length) {
        _desName = [folder lastPathComponent];
    }
    
    NSString* _desPngPath = [[[folder stringByDeletingLastPathComponent] stringByAppendingPathComponent:_desName] stringByAppendingPathExtension:@"png"];
    NSString* _desFntPath = [[[folder stringByDeletingLastPathComponent] stringByAppendingPathComponent:_desName] stringByAppendingPathExtension:@"fnt"];
    NSFileManager* fmg = [NSFileManager defaultManager];
    
    [fmg removeItemAtPath:_desPngPath error:nil];
    [fmg removeItemAtPath:_desFntPath error:nil];
    
    _strFnt = [NSMutableString string];
    
    NSString* _extension = extension;
    if (!_extension.length) {
        _extension = @"png";
    }
    NSDictionary* imgs = allImgs(folder, _extension);
    float maxw = [maxWidth floatValue];
    
    if (!maxw) {
        maxw = 1024;
    }
    
    if (!imgs.count) {
        printf("fnttool makeFnt failed, no image found in %s\n", folder.UTF8String);
        return;
    }
    
    float l = 0;
    float t = 0;
    float desw = 0;
    
    NSString* key = imgs.allKeys.firstObject;
    CGImageRef img = (__bridge CGImageRef)(imgs[key]);
    size_t w = CGImageGetWidth(img);
    size_t h = CGImageGetHeight(img);
    
    for (int i = 0; i < imgs.count; i++) {
        if (l + w < maxw) {
            l += w;
            if (l > desw) {
                desw = l;
            }
        }
        else {
            l = w;
            t += h;
        }
    }
    
    t += h;
    
    [_strFnt appendFormat:@"info face=\"Arial\" size=%zu bold=0 italic=0 charset=\"\" unicode=0 stretchH=100 smooth=1 aa=1 padding=0,0,0,0 spacing=2,2\n", h];
    [_strFnt appendFormat:@"common lineHeight=%lu base=20 scaleW=%d scaleH=%d pages=1 packed=0\n", h + 20, (int)desw, (int)t];
    [_strFnt appendFormat:@"page id=0 file=\"%@\"\n", [_desPngPath lastPathComponent]];
    [_strFnt appendFormat:@"chars count=%lu\n", (unsigned long)imgs.count];
    
    //create des bit map
    CGColorSpaceRef colorSpace = CGColorSpaceCreateDeviceRGB();
    CGContextRef context = CGBitmapContextCreate(NULL,
                                                 desw,
                                                 t,
                                                 8,
                                                 desw * 8,
                                                 colorSpace,
                                                 kCGBitmapAlphaInfoMask & kCGImageAlphaPremultipliedLast);
    
    CGColorSpaceRelease(colorSpace);
    
    if (context == NULL) {
        printf("failed to create the output bitmap context! %f %f \n", desw, t);
    }

    l = 0;
    t = 0;
    
    NSMutableArray* key_tmp = [NSMutableArray arrayWithArray:imgs.allKeys];
    
    [key_tmp sortUsingComparator:^NSComparisonResult(id  _Nonnull obj1, id  _Nonnull obj2) {
        return [obj1 compare:obj2 options:NSNumericSearch];
    }];
    
    for (int i = 0; i < key_tmp.count; i++) {
        NSString* key = key_tmp[i];
        CGImageRef img = (__bridge CGImageRef)(imgs[key]);
        
        size_t w = CGImageGetWidth(img);
        size_t h = CGImageGetHeight(img);

        CGRect destTile = CGRectMake(l, t, w, h);
        CGContextDrawImage(context, destTile, img);
        
        [_strFnt appendFormat:@"char id=%d x=%d y=%d width=%zu height=%zu xoffset=0 yoffset=0 xadvance=%zu page=0 chnl=0 letter=\"%@\"\n", (int)key.UTF8String[0], (int)l, (int)t, w, h, w, key];
        
        if (l + w < maxw) {
            l += w;
        }
        else {
            l = w;
            t += h;
        }
    }
    
    CGImageRef destImage = CGBitmapContextCreateImage(context);
    CGImageWriteToFile(destImage, _desPngPath);
    
    [_strFnt writeToFile:_desFntPath atomically:YES encoding:NSUTF8StringEncoding error:nil];
}

int main(int argc, const char * argv[]) {
    @autoreleasepool {
        NSMutableArray* args = [NSMutableArray array];
        for (int i = 0; i < argc; i++) {
            [args addObject:[NSString stringWithUTF8String:argv[i]]];
        }
        
        NSMutableArray *keys = [NSMutableArray array];
        NSMutableArray *values = [NSMutableArray array];

        bool start = false;
        for (int i = 0; i < argc; i++) {
            
            if ([args[i] hasPrefix:@"-"]) {
                [keys addObject:[args[i] substringFromIndex:1]];
                start = true;
            }
            else {
                if (start) {
                    [values addObject:args[i]];
                }
            }
        }
        
        if (!keys.count || keys.count != values.count) {
            printf("\n***** fnttool *****\n");
            printf("\t参数:\n");
            printf("\t-i key\t\t\tSearch document by keyword 搜索 key 对应的文档描述\n");
            printf("\t-f folder_path\t\tUsing files in folder 使用文件夹内的文件\n");
            printf("\t-e extension\t\tOnly use files with specified extension 文件夹内仅搜索这类扩展名\n");
            printf("\t-d filename\t\tDestination file name 指定创建的fnt文件名\n");
            printf("\t-w max_width\t\tSet the fnt png image's max width 创建的fnt图片文件最大宽度，默认1024\n");
            
            return -1;
        }
        
        _params = [NSDictionary dictionaryWithObjects:values forKeys:keys];
        if ([_params[@"i"] length]) {
            NSLog(@"%@", searchInfo(_params[@"i"]));
            return 0;
        }
        
        if ([_params[@"f"] length]) {
            makeFnt(_params[@"f"], _params[@"e"], _params[@"d"], _params[@"w"]);
        }
    }
    return 0;
}
