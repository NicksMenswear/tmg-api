import json

def data_extractor(response, variant_id):

    try:
        product_details = response
        product = product_details.get('product', {})
        product_id = product.get('id')
        title = product.get('title')
        vendor = product.get('vendor')
        body_html = product.get('body_html')
        images = product.get('images')
        variants = product.get('variants', [])
        specific_variant = [variant for variant in variants if str(variant['id']) == str(variant_id)]
        if specific_variant:
            specific_variant = specific_variant[0]
        else:
            specific_variant = None
        
        return {
            'product_id': product_id,
            'title': title,
            'vendor': vendor,
            'body_html': body_html,
            'images': images,
            'specific_variant': specific_variant
        }
    except Exception as e:
        print(e)