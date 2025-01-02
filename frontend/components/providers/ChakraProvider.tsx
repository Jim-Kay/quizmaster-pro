'use client'

import { ChakraProvider as ChakraUIProvider } from '@chakra-ui/react'
import { CacheProvider } from '@chakra-ui/next-js'

export default function ChakraProvider({ 
    children 
}: { 
    children: React.ReactNode 
}) {
    return (
        <CacheProvider>
            <ChakraUIProvider>
                {children}
            </ChakraUIProvider>
        </CacheProvider>
    )
}
