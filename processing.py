def cast_categories(df):
    """Cast ordered categories to 'cut', 'color', and 'clarity' columns."""

    df['cut'] = (df['cut']
                 .astype('category')
                 .cat.set_categories(['Fair', 'Good', 'Very Good', 'Ideal',
                                      'Super Ideal'], ordered=True)
                 )
    df['color'] = (df['color']
                   .astype('category')
                   .cat.set_categories(['J', 'I', 'H', 'G', 'F', 'E', 'D'],
                                       ordered=True)
                   )
    df['clarity'] = (df['clarity']
                     .astype('category')
                     .cat.set_categories(['SI2', 'SI1', 'VS2', 'VS1', 'VVS2',
                                          'VVS1', 'IF', 'FL'], ordered=True)
                     )
