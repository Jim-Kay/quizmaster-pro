'use client'

import { Button as ChakraButton } from '@chakra-ui/react'
import { forwardRef } from 'react'

export const Button = forwardRef<HTMLButtonElement, any>((props, ref) => {
  return <ChakraButton ref={ref} {...props} />
})

Button.displayName = 'Button'

export { Button as default }
